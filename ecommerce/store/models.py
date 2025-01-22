from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

# Create your models here.


from django.db import models
from django.contrib.auth.models import User

class Admin(models.Model):
	user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)  # Links to Django's User model
	email = models.EmailField(unique=True)
	password = models.CharField(max_length=128)

	def __str__(self):
		return self.user.username if self.user else self.email


class Seller(models.Model):
	admin = models.ForeignKey(Admin, on_delete=models.CASCADE, related_name="sellers")  # Links Seller to Admin
	company_name = models.CharField(max_length=100)
	product_type = models.CharField(max_length=50)
	email = models.EmailField(unique=True)
	password = models.CharField(max_length=128)
	mobile_number = models.CharField(max_length=15)

	

	def __str__(self):
		return self.company_name


class Customer(models.Model): 
	pro_img = models.ImageField(null=True, blank=True)
	firstname = models.CharField(max_length=200, null=False, blank=False,default='')
	lastname = models.CharField(max_length=100, null=True, blank=True)
	email = models.EmailField(unique=True)  # Ensure email uniqueness
	mobile_number = models.CharField(max_length=15,null=False,blank=False)
	home_address = models.TextField(null=True,blank=True)
	work_address = models.TextField(null=True,blank=True)
	password = models.CharField(max_length=255, null=False, blank=False,default='')  # Store hashed passwords
	confirm_password = models.CharField(max_length=255, null=False, blank=False,default='')  # Store hashed passwords
	last_login = models.DateTimeField(auto_now=True)
	

	# def save(self, *args, **kwargs):
	# 	# Hash the password before saving
	# 	if not self.pk:  # Only hash if the object is being created
	# 		self.password = make_password(self.password)
	# 		self.confirm_password = make_password(self.confirm_password)
	# 	super().save(*args, **kwargs)
	
	@property
	def is_authenticated(self):
		# Always return True for instances representing authenticated users
		return True

	@property
	def imageURL(self):
		try:
			url = self.pro_img.url   #.URL returns the publicly accessible URL of the file
		except:
			url = ''  
		return url


	def __str__(self):
		return self.firstname

#Create your models here.
class Catagory(models.Model):
	catagory_name = models.CharField(max_length=150, null=False, blank=False)
	cat_image = models.ImageField(null=True, blank=True)
	Description = models.TextField(max_length=500, null=False, blank=False)
	status = models.BooleanField(default=False, help_text="0-Show,1-Hidden")
	created_at = models.DateTimeField(auto_now_add=True)

	@property
	def imageURL(self):
		try:
			url = self.cat_image.url   #.URL returns the publicly accessible URL of the file
		except:
			url = ''
		return url

	def __str__(self):
		return self.catagory_name

class Product(models.Model):
	seller = models.ForeignKey(Seller,on_delete=models.CASCADE,null=True)
	catagory_name = models.ForeignKey(Catagory,on_delete=models.CASCADE)

	name = models.CharField(max_length=200, null=False, blank=False)
	price = models.FloatField()
	description = models.TextField(max_length=500, null=False, blank=False, default="product_description")
	vendor = models.CharField(max_length=150, null=False, blank=False, default="vendor")
	quantity = models.IntegerField(null=False, blank=False, default=0)
	digital = models.BooleanField(default=False, null=True, blank=True)
	image = models.ImageField(null=True, blank=True)

		#if image not available
	@property
	def imageURL(self):
		try:
			url = self.image.url   #.URL returns the publicly accessible URL of the file
		except:
			url = ''
		return url
	
	def __str__(self):
		return self.name



class Order(models.Model):
	customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)   #Foreign key Customer can order many time many to one relationship 
	date_ordered = models.DateTimeField(auto_now_add=True)
	complete = models.BooleanField(default=False)
	transaction_id = models.CharField(max_length=100, null=True)

	def __str__(self):
		return str(self.id)
		
	@property
	def shipping(self):
		shipping = False
		orderitems = self.orderitem_set.all()  # you can access all related OrderItem objects using the orderitem_set attribute
		for i in orderitems:
			if i.product.digital == False: #order item class foreign key with order item orderitem hav product product.digital
				shipping = True
		return shipping

	@property
	def get_cart_total(self):
		orderitems = self.orderitem_set.all()
		total = sum([item.get_total for item in orderitems])
		return total 

	@property
	def get_cart_items(self):
		orderitems = self.orderitem_set.all()
		total = sum([item.quantity for item in orderitems])
		return total 

class OrderItem(models.Model):
	product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
	order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
	quantity = models.IntegerField(default=0, null=True, blank=True)
	date_added = models.DateTimeField(auto_now_add=True)

	@property
	def get_total(self):
		total = self.product.price * self.quantity
		return total
	def __int__(self):
		return self.product

class ShippingAddress(models.Model):
	customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
	order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
	address = models.CharField(max_length=200, null=False)
	city = models.CharField(max_length=200, null=False)
	state = models.CharField(max_length=200, null=False)
	zipcode = models.CharField(max_length=200, null=False)
	date_added = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.address
	
	@property
	def shipping(self):
		shipping = False
		orderitems = self.orderitem_set.all()
		for i in orderitems:
			if i.product.digital == False:
				shipping = True
		return shipping


class Favourite(models.Model):
	customer = models.ForeignKey(Customer,on_delete=models.CASCADE)
	product = models.ForeignKey(Product,on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return str(self.customer)

class Coupon(models.Model):
	code = models.CharField(max_length=20, unique=True)
	discount = models.DecimalField(max_digits=5, decimal_places=2)  # Percentage or fixed value
	valid_from = models.DateTimeField()
	valid_to = models.DateTimeField()
	active = models.BooleanField(default=True)

	def __str__(self):
		return self.code



