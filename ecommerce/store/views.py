from django.shortcuts import render,redirect
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.contrib import messages
import json
from django.utils.timezone import now
import datetime
from .models import * 
from .utils import cookieCart, cartData, guestOrder
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.hashers import check_password
import logging
from decimal import Decimal


from store import form
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes 
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group
from .form import  ForgotPasswordForm, ResetPasswordForm 
from .tokens import custom_token_generator

#Store

def store(request):
	data = cartData(request)
	customer_id = request.session.get('customer_id')
	products = Product.objects.all()
	cartItems = data['cartItems']
	order = data['order']
	items = data['items']
	catagory = Catagory.objects.filter(status=0)
	#---------------
	name_filter = request.GET.get('name', '')
	min_price = request.GET.get('min_price', '')
	max_price = request.GET.get('max_price', '')

	# Apply name filter
	if name_filter:
		products = products.filter(name__icontains=name_filter)
	if min_price:
		products = products.filter(price__gte=min_price)
	# Apply price range filter
	if max_price:
		products = products.filter(price__lte=max_price)

	#---------------
	
	if customer_id:
		customer = Customer.objects.get(id=customer_id)
	else:
		customer = "Guest"
	#---------------
	
	favorite_product_names = set(Favourite.objects.filter(customer_id=customer_id).values_list('product__name', flat=True)) if customer_id else set()	
	print(favorite_product_names)

	itm = []
	if customer_id:	
		for item in items:
			#product_id = item['product']['id']
			product_id = item.product.id
			itm.append(product_id)
	else:	
		for item in items:
			product_id = item['product']['id']
			# product_id = item.product.id
			itm.append(product_id)
			

	print(itm)
	# print(items)

	context = {'products':products, 'cartItems':cartItems,'user': customer, 'favorite_product_names': favorite_product_names,"catagory":catagory,'itm':itm,'items':items}
	return render(request, 'store/store.html', context)

#Cart

def cart(request):
	data = cartData(request)

	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/cart.html', context)

#CheckOut

def checkout(request):
	# Retrieve cart data
	data = cartData(request)
	cartItems = data['cartItems']
	order = data['order']
	items = data['items']
	total= 0
	original_total = 0
	
	# Handle coupon application via input field in the POST request
	coupon_code = request.POST.get('coupon_code', '').strip()  # Get the coupon code from the input field
	
	if coupon_code:
		try:
			# Calculate the original cart total (before applying any coupon)
			original_total = order.get_cart_total

			
			# Initialize the total price with the original total
			total = Decimal(original_total)
			# Try to fetch the coupon based on the code
			coupon = Coupon.objects.get(code=coupon_code, active=True, valid_from__lte=now(), valid_to__gte=now())
			# Apply discount (percentage discount assumed)
			discount = coupon.discount
			total -= total * (discount / 100)
			# Save coupon ID in session for persistence
			request.session['coupon_id'] = coupon.id
			messages.success(request, f"Coupon '{coupon.code}' applied successfully! Discount: {discount}%")
		except Coupon.DoesNotExist:
			messages.error(request, "Invalid or expired coupon.")
	
	# Update the order with the total price after applying the discount
	order_total = total
	
	# Send both original and discounted prices to the template
	context = {
		'items': items,
		'order': order,
		'cartItems': cartItems,
		'original_total': original_total,
		'order_total': order_total,
	}
	return render(request, 'store/checkout.html', context)

#Cart_Quantity update

def updateItem(request):
	data = json.loads(request.body)
	productId = data['productId']
	action = data['action']
	print('Action:', action)
	print('Product:', productId)

	logger = logging.getLogger("Testing")
	logger.debug(f"the values are {action}")

	# Retrieve customer based on session data
	# customer_id = request.session.get('customer_id',)  # Get the customer_id from the session
	customer_id = request.session.get('customer_id')  # Use 'AnonymousUser' as the default value

	try:
		customer = Customer.objects.get(id=customer_id)  # Fetch customer object using customer_id
	except Customer.DoesNotExist:
		return JsonResponse({'status': 'error', 'message': 'Customer not found'}, status=404)

	# customer = request.user.customer
	product = Product.objects.get(id=productId)
	order, created = Order.objects.get_or_create(customer=customer, complete=False)

	orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

	if action == 'add':
		orderItem.quantity = (orderItem.quantity + 1)
	elif action == 'remove':
		orderItem.quantity = (orderItem.quantity - 1)

	if orderItem.quantity <= product.quantity:
		orderItem.save()
	else:
		return JsonResponse({'status': 'Out of Stock'}, status=200)

	if orderItem.quantity <= 0:
		orderItem.delete()
	
	return JsonResponse({'status': 'Item was added'}, status=200 ,safe=False)
	# # return render(request,'store/store.html',{})
	# return JsonResponse('Item was added', safe=False)

def processorder(request):
	transaction_id = datetime.datetime.now().timestamp()
	data = json.loads(request.body)

	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
	else:
		customer, order = guestOrder(request, data)

	total = float(data['form']['total'])
	order.transaction_id = transaction_id

	if total == order.get_cart_total:
		order.complete = True
	order.save()

	if order.shipping == True:
		ShippingAddress.objects.create(
		customer=customer,
		order=order,
		address=data['shipping']['address'],
		city=data['shipping']['city'],
		state=data['shipping']['state'],
		zipcode=data['shipping']['zipcode'],
		)

	return JsonResponse('Payment submitted..', safe=False)

#Login ,register,logout

def register(request):
	if request.method == 'POST':
		# data = json.loads(request.body)
		# email = data.get('email')
		# password = data.get('password')
		# confirm_password = data.get('confirm_password')
		firstname = request.POST['firstname']
		lastname = request.POST['lastname']
		email = request.POST['email']
		password = request.POST['password']
		confirm_password = request.POST['confirm_password']

		if not email or not password or not confirm_password or not firstname:
			return JsonResponse({'status': 'error', 'message': 'All fields are required'})

		elif password != confirm_password:
			return JsonResponse({'status': 'error', 'message': 'Passwords do not match'})

		elif Customer.objects.filter(email=email).exists():
			return JsonResponse({'status': 'error', 'message': 'Email already registered'})
		
		else:
		# Create and save the customer
			Customer.objects.create(firstname=firstname,lastname=lastname,email=email, password=password,confirm_password=confirm_password)
			messages.success(request, "Registration successful!")
			return redirect('login')  
	
	return render(request, 'store/register.html')


def login_view(request):
	if request.method == 'POST':
		# email = request.POST['email']
		# password = request.POST['password']
		email = request.POST.get('email')
		password = request.POST.get('password')

		try:
			customer = Customer.objects.get(email=email)
		
				# Check if the password matches
			if password == customer.password:
				# Manually authenticate the user (custom authentication)
				request.session['customer_id'] = customer.id
				request.session['imageURL'] = customer.imageURL
				# print(customer.imageURL) 
				# request.session.modified = True

				messages.success(request, "Login successful!")
				return redirect('store')
			else:
				messages.error(request, "Invalid Password")
				return redirect('login')
			
		except Customer.DoesNotExist:
			messages.error(request, "Invalid email or password")
			return redirect('login')  # Redirect to login page



	return render(request, 'store/login.html')


def logout_view(request):
	if 'customer_id' in request.session:
		del request.session['customer_id']  # Remove customer ID from session
		del request.session['imageURL']
		# request.session['customer_id'] = 'AnonymousUser'
		request.session.modified = True    # Ensure session is updated
	elif 'seller_id' in request.session:
		del request.session['seller_id']  # Remove customer ID from session
	messages.success(request, "You have been logged out!")
	return redirect('login')

#Favorite

def updateFavorite(request):
	if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
		if 'customer_id' in request.session:
			try:
				data = json.loads(request.body)
				productId = data.get('productId')
				action = data.get('action')
				customer_id = request.session.get('customer_id')

				if not productId or not action:
					return JsonResponse({'status': 'Invalid request data'}, status=400)

				customer = Customer.objects.get(id=customer_id)
				product = Product.objects.get(id=productId)

				if action == 'add':
					if Favourite.objects.filter(customer=customer, product=product).exists():
						return JsonResponse({'status': 'Item already added to favorites'}, status=200)

					Favourite.objects.create(customer=customer, product=product)
					return JsonResponse({'status': 'Item successfully added to favorites'}, status=200)

				elif action == 'remove':
					favorite_item = get_object_or_404(Favourite, product__id=productId, customer=customer)
					favorite_item.delete()
					return JsonResponse({'status': 'Item removed from favorites'}, status=200)

				else:
					return JsonResponse({'status': 'Invalid action'}, status=400)

		   
			except Exception as e:
				return JsonResponse({'status': f'Error: {str(e)}'}, status=500)
		else:
			return redirect('login')
			# return JsonResponse({'status': 'Login to add favorite items'}, status=401)

	return JsonResponse({'status': 'Invalid request'}, status=400)


def favData(request):
	if 'customer_id' in request.session:
		customer = request.session.get('customer_id')
		favorites = Favourite.objects.filter(customer=customer)
		return {'favorites': favorites}
	else:
		return {'favorites': []}


def favPage(request):
	if 'customer_id' in request.session:
		data = cartData(request)
		cartItems = data['cartItems']
		data = favData(request)
		favorites = data['favorites']

		return render(request, 'store/fav.html', {'items': favorites,'cartItems':cartItems})
	else:
		return redirect('login')


def removeFavorite(request, id):
	if 'customer_id' in request.session:
		customer = request.session.get('customer_id')
		
		favorite_item = get_object_or_404(Favourite, id=id,customer__id=customer)
		favorite_item.delete()
		return redirect('favviewpage')
	else:
		return redirect('login')


#profile

def update_profile(request, id):
	if request.method == "POST":
		customer = get_object_or_404(Customer, id=id)
		customer.firstname = request.POST.get('firstname')
		customer.lastname = request.POST.get('lastname')
		customer.email = request.POST.get('email')
		customer.mobile_number = request.POST.get('mobilenumber')
		# if 'proimg' in request.FILES:
		customer.pro_img = request.FILES['proimg']
		customer.save()
		messages.success(request, "Profile updated successfully!")
		return redirect('profile', id=id)

def update_address(request, id):
	if request.method == "POST":
		customer = get_object_or_404(Customer, id=id)
		customer.home_address = request.POST.get('home_address')
		customer.work_address = request.POST.get('work_address')
		customer.save()
		messages.success(request, "Address updated successfully!")
		return redirect('profile', id=id)

def profile(request, id):
	customer_id = request.session.get('customer_id')
	if customer_id:
		try:
			customer = Customer.objects.get(id=customer_id)
			data = cartData(request)
			cartItems = data['cartItems']
			order = data['order']
			items = data['items']

			fav_data = favData(request)
			favorites = fav_data['favorites']

			order_status = Order.objects.filter(customer=customer)
			print(order_status)
			order_id = [order.id for order in order_status]
			print(order_id)
			# order_item = OrderItem.objects.filter(order__in=order_id)
			# print(order_item)
			order_item = OrderItem.objects.filter(order__in=order_status)
			# print(order_item)

			order_completion_count = 0
			for order in order_status:
				if order.complete:
					order_completion_count+=1

			ShippingAdd = ShippingAddress.objects.all()

			# for item in ShippingAdd:
			# 	if item.order in order_status:
			# 		print(item.order)
			# for data in order_item:
			# 	print(data.order)
			# 	if data.order in order_status:
			# 		print(data.product)
			# print(ShippingAdd)
			# for item in ShippingAdd:
			# 	print(item.order)
			# addr=set()
			# for data in order_item:
			# 	for item in ShippingAdd:
			# 		if data.order == item.order:
			# 			if item not in addr:
			# 				addr.add(item.order.id)
					
			# print(addr)

			context = {
				'items': items,
				'order': order,
				'cartItems': cartItems,
				'customer': customer,
				'fav':favorites,
				'order_status':order_status,
				'order_item':order_item,
				'order_completion_count':order_completion_count,
				'ShippingAdd':ShippingAdd
			}
			
			return render(request, 'store/profile.html', context)
		except Customer.DoesNotExist:
			messages.error(request, "No customer data available")
			return redirect('login')
	else:
		messages.error(request, "No customer data available")
		return redirect('login')

#Product Details

def product_details(request,product_id):
	customer_id  = request.session.get('customer_id')
	product = Product.objects.get(id=product_id)
	favorite_product_names = set(Favourite.objects.filter(customer_id=customer_id).values_list('product__name', flat=True)) if customer_id else set()	
	# print(favorite_product_names)
	return render(request,"store/product/product_details.html",{'product':product,'favorite_product_names':favorite_product_names})

#Admin

def admin_login_view(request):
	if request.method == 'POST':
		email = request.POST.get('email')
		password = request.POST.get('password')

		try:
			# Retrieve the admin by email
			admin = Admin.objects.get(email=email)

			# Check if the password matches
			if password == admin.password:
				# Store admin in session (custom authentication)
				request.session['admin_id'] = admin.id

				# Display success message and redirect
				messages.success(request, "Login successful!")
				return redirect('admin_dashboard')  # Replace 'admin_view' with your dashboard view name
			else:
				messages.error(request, "Invalid email or password.")
		except Admin.DoesNotExist:
			messages.error(request, "No account found with this email!")

		# Redirect back to login on failure
		return redirect('admin_login')

	# Render login page for GET requests
	return render(request, 'store/auth/admin_login.html')


def seller_reg(request):
	if request.method == "POST":
		company_name = request.POST['company_name']
		product_type = request.POST['product_type']
		email = request.POST['email']
		password = request.POST['password']
		mobile_number = request.POST['mobile_number']

		# Find Admin for the logged-in user
		try:
			admin = Admin.objects.get(user=request.user)
			logger = logging.getLogger("Testing")
			logger.debug(f"the values are {admin}")
		except Admin.DoesNotExist:
			messages.error(request, "Admin account not found. Please contact support.")
			return redirect('admin_view')


		# Create Seller
		Seller.objects.create(
			admin=admin,
			company_name=company_name,
			product_type=product_type,
			email=email,
			password=password,  # Hash password
			mobile_number=mobile_number
		)
		messages.success(request, "Seller registered successfully!")
		return redirect('admin_dashboard')

	return render(request, 'store/auth/admin_view.html')


def admin_dashboard(request):
	admin = get_object_or_404(Admin, user=request.user)
	sellers = admin.sellers.all()  # Fetch sellers linked to the logged-in admin
	return render(request, 'store/auth/admin_dashboard.html', {'sellers': sellers,'admin':admin})


def removeseller(request, id):
	admin = get_object_or_404(Admin, user=request.user)
	seller = get_object_or_404(Seller, id=id,admin=admin)
	seller.delete()
	return redirect('admin_dashboard')
	# return JsonResponse({'status':"Seller deleted successfully"},status=200)

#seller

def seller_login(request):
	if request.method == 'POST':
		email = request.POST.get('email')
		password = request.POST.get('password')

		try:
			# Retrieve the admin by email
			seller = Seller.objects.get(email=email)

			# Check if the password matches
			if password == seller.password:
				# Store admin in session (custom authentication)
				request.session['seller_id'] = seller.id

				# Display success message and redirect
				messages.success(request, "Login successful!")
				return redirect('seller_dashboard')  # Replace 'admin_view' with your dashboard view name
			else:
				messages.error(request, "Invalid email or password.")

		except Seller.DoesNotExist:
			messages.error(request, "No account found with this email!")

	# Redirect back to login on failure
		return redirect('seller_login')

	# Render login page for GET requests
	return render(request, 'store/seller/seller_login.html')

def seller_product_upload(request, id=None):
	categories = Catagory.objects.all()
	seller_id = request.session.get('seller_id')
	seller = Seller.objects.get(id=seller_id)

	product = None
	selected_category_id = None  # Default value for a new product

	if id:
		product = get_object_or_404(Product, id=id)
		selected_category_id = product.catagory_name.id  # Get the category for an existing product

	if request.method == "POST":
		# Get data from the form
		category_id = request.POST['catagory_name']
		product_name = request.POST.get('product_name')
		vendor_name = request.POST.get('vendorname')
		description = request.POST.get('description')
		price = request.POST.get('price')
		quantity = request.POST.get('quantity')
		digital = request.POST.get('digital') == "yes"
		product_image = request.FILES.get('formfile')

		if product:  # Update existing product
			product.catagory_name = Catagory.objects.get(id=category_id)
			product.name = product_name
			product.vendor = vendor_name
			product.description = description
			product.price = price
			product.quantity = quantity
			product.digital = digital
			if product_image:  # Update image only if a new one is provided
				product.image = product_image
			product.save()
			messages.success(request, "Product updated successfully!")
			return redirect('seller_dashboard')
		else:  # Create a new product
			category = Catagory.objects.get(id=category_id)
			product = Product.objects.create(
				seller=seller,
				catagory_name=category,
				name=product_name,
				price=price,
				description=description,
				vendor=vendor_name,
				quantity=quantity,
				digital=digital,
				image=product_image
			)
			messages.success(request, "Product uploaded successfully!")
			return redirect('seller_dashboard')

	return render(request, 'store/seller/seller_product_upload.html', {
		'categories': categories,
		'product': product,
		'selected_category_id': selected_category_id
	})

def seller_dashboard(request):
	seller_id = request.session.get('seller_id')
	seller = Seller.objects.get(id = seller_id)
	product =  Product.objects.filter(seller=seller)
	print(product)
	return render(request, 'store/seller/seller_dashboard.html', {'sellers': seller,'product':product})

def remove_product(request,id):
	if 'seller_id' in request.session:
		seller = request.session.get('seller_id')
		product = get_object_or_404(Product, id=id,seller=seller)
		product.delete()
		return redirect('seller_dashboard')
	else:
		return redirect('login')

#Collections

def collections(request):
	data = cartData(request)
	cartItems = data['cartItems']
	catagory = Catagory.objects.filter(status=0)
	return render(request,'store/collections.html',{"catagory":catagory,"cartItems":cartItems})

def collectionsview(request, catagory_name):
	if Catagory.objects.filter(catagory_name=catagory_name, status=0).exists():
		products = Product.objects.filter(catagory_name__catagory_name=catagory_name)
		return render(request, 'store/product/index.html', {"products": products, "category": catagory_name})
	else:
		messages.warning(request, "No details are available for the selected category.")
		return redirect('store/collections')

#forget password

def forgot_password(request):
	form = ForgotPasswordForm()
	if request.method == 'POST':
		#form
		form = ForgotPasswordForm(request.POST)
		if form.is_valid():
			email = form.cleaned_data['email']
			print(email)
			try:
				user = Customer.objects.get(email=email)
				#send email to reset password
				token = custom_token_generator.make_token(user)
				uid = urlsafe_base64_encode(force_bytes(user.pk))
				current_site = get_current_site(request)
				domain = current_site.domain
				subject = "Reset Password Requested"
				message = render_to_string('store/reset_password_email.html', {
					'domain': domain,
					'uid': uid,
					'token': token
				})

				send_mail(subject, message, 'noreply@gmail.com', [email])
				messages.success(request, 'Email has been sent')
			except Customer.DoesNotExist:
				print("No Mail Found")
				messages.error(request,'No account fount with this email')

	return render(request,'store/forget_password.html', {'form': form})


def reset_password(request, uidb64, token):
	form = ResetPasswordForm()
	if request.method == 'POST':
		#form
		form = ResetPasswordForm(request.POST)
		if form.is_valid():
			new_password = form.cleaned_data['new_password']
			try:
				uid = urlsafe_base64_decode(uidb64)
				user = Customer.objects.get(pk=uid)
			except(TypeError, ValueError, OverflowError, User.DoesNotExist):
				user = None

			if user is not None and custom_token_generator.check_token(user, token):
				user.password = new_password
				user.confirm_password = new_password
				user.save()
				messages.success(request, 'Your password has been reset successfully!')
				return redirect('login')
			else :
				messages.error(request,'The password reset link is invalid')

	return render(request,'store/reset_password.html', {'form': form})



