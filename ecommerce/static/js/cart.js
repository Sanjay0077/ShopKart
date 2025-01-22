var updateBtns = document.getElementsByClassName('update-cart')

// var customerId = document.getElementById('customer-id') ? document.getElementById('customer-id').value : 'AnonymousUser';
var customerId =  document.getElementById('customer-id').value;

console.log(customerId)
for (i = 0; i < updateBtns.length; i++) {
	updateBtns[i].addEventListener('click', function(){
		var productId = this.dataset.product
		var action = this.dataset.action

		console.log('productId:', productId, 'Action:', action)
		console.log('USER:', customerId);

		if (customerId === 'AnonymousUser') {
			// Handle anonymous users by adding to cookies
			addCookieItem(productId, action);
		} else {
			// Handle logged-in users by updating their order

			updateUserOrder(productId, action);


		}
	})
}


// Handle "+" and "−" buttons in the quantity input group
document.querySelectorAll('.btn-minus').forEach((button) => {
    button.addEventListener('click', function () {
        const productId = this.dataset.product;
        updateUserOrder(productId, 'remove');
    });
});

document.querySelectorAll('.btn-plus').forEach((button) => {
    button.addEventListener('click', function () {
        const productId = this.dataset.product;
        updateUserOrder(productId, 'add');
    });
});

function updateUserOrder(productId, action){
	console.log('User is authenticated, sending data...')

		var url = '/update_item/'

		fetch(url, {
			method:'POST',
			headers:{
				'Content-Type':'application/json',
				'X-CSRFToken':csrftoken,
			}, 
			body:JSON.stringify({'productId':productId, 'action':action})
		})
		.then((response) => {
		   return response.json();
		})
		.then((data) => {
			location.reload()
		});
}


function addCookieItem(productId, action){
	console.log('User is not authenticated')

	if (action == 'add'){
		if (cart[productId] == undefined){
		cart[productId] = {'quantity':1}

		}else{
			
			cart[productId]['quantity'] += 1
		}
	}

	if (action == 'remove'){
		cart[productId]['quantity'] -= 1

		if (cart[productId]['quantity'] <= 0){
			console.log('Item should be deleted')
			delete cart[productId];
		}
	}
	console.log('CART:', cart)
	document.cookie ='cart=' + JSON.stringify(cart) + ";domain=;path=/"
	
	location.reload()
}




