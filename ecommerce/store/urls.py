from django.urls import path # type: ignore
from . import views

#"url paths" to call these views.
urlpatterns = [
    path('',views.store, name="store"),
    path('cart/',views.cart, name="cart"),
    path('checkout/',views.checkout, name="checkout"),

    path('favviewpage/', views.favPage, name='favviewpage'),  # Favorites view page
    path('updateFavorite/', views.updateFavorite, name='updateFavorite'),  # Add to favorites
    path('removeFavorite/<int:id>/', views.removeFavorite, name='removeFavorite'),

    path('update_item/',views.updateItem, name="UpdateItem"),
    path('process_order/',views.processorder,name="process_order"),

    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('profile/<int:id>/', views.profile, name='profile'),

    path('product_details/<int:product_id>/', views.product_details, name='product_details'),
    
    path('admin_login',views.admin_login_view,name='admin_login'),
    path('seller_reg', views.seller_reg, name='seller_reg'),
    path('admin_dashboard', views.admin_dashboard, name='admin_dashboard'),
    path('removeseller/<int:id>/', views.removeseller, name='removeseller'),
    

    path('seller_login',views.seller_login,name='seller_login'),
    path('seller_product_upload',views.seller_product_upload,name="seller_product_upload"),
    path('seller_product_upload/<int:id>',views.seller_product_upload,name="seller_product_upload"),
    path('seller_dasboard',views.seller_dashboard,name="seller_dashboard"),
    # path('edit_product/<int:id>',views.edit_product,name="edit_product"),
    path('remove_product/<int:id>',views.remove_product,name="remove_product"),
    
    path('update_address/ <int:id>',views.update_address,name="update_address"),
    path('update_profile/ <int:id>',views.update_profile,name="update_profile"),

    path('collections', views.collections,name='collections'),
    path('collections/<str:catagory_name>', views.collectionsview, name='collectionsview'),

    path("forgot_password", views.forgot_password, name="forgot_password" ),
    path("reset_password/<uidb64>/<token>", views.reset_password, name="reset_password" ),
]

    # path('admin_view',views.admin_view,name='admin_view'),