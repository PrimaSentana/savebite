from sqladmin import ModelView

from app.models.menu import Menu
from app.models.merchants import Merchant
from app.models.review import Review
from app.models.transaction import Order
from app.models.user import User

class UserAdmin(ModelView, model=User):
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-users"
    
    column_list = [
        User.id,
        User.username,
        User.email,
        User.is_active,
        User.created_at
    ]
    column_searchable_list = [User.username, User.email]
    column_sortable_list = [User.id, User.username, User.created_at]
    # column_filters = [User.is_active]
    
    form_excluded_columns = [User.password]
    column_details_exclude_list = [User.password]
    
    can_create = False
    can_delete = True
    can_edit = True
    can_view_details = True
    
class MerchantAdmin(ModelView, model=Merchant):
    name = "Merchant"
    name_plural = "Merchants"
    icon = "fa-solid fa-store"
    
    column_list = [
        Merchant.id,
        Merchant.name,
        Merchant.email,
        Merchant.phone,
        Merchant.is_active,
        Merchant.is_open,
        Merchant.balance,
        Merchant.average_rating,
        Merchant.review_count,
        Merchant.created_at,
    ]
    column_searchable_list = [Merchant.name, Merchant.email, Merchant.phone]
    column_sortable_list = [
        Merchant.id,
        Merchant.name,
        Merchant.balance,
        Merchant.average_rating,
        Merchant.created_at,
    ]
    # column_filters = [Merchant.is_active]
    
    form_excluded_columns = [Merchant.password]
    column_details_exclude_list = [Merchant.password]
    
    can_create = False
    can_delete = True
    can_edit = True
    can_view_details = True
    
class MenuAdmin(ModelView, model=Menu):
    name = "Menu"
    name_plural = "Menus"
    icon = "fa-solid fa-utensils"
    
    column_list = [
        Menu.id,
        Menu.title,
        Menu.category,
        Menu.original_price,
        Menu.discounted_price,
        Menu.discount_percentage,
        Menu.quantity,
        Menu.status,
        Menu.is_active,
        Menu.available_from,
        Menu.available_until,
        Menu.created_at,
    ]
    column_searchable_list = [Menu.title]
    column_sortable_list = [
        Menu.id,
        Menu.title,
        Menu.discounted_price,
        Menu.discount_percentage,
        Menu.quantity,
        Menu.created_at,
    ]
    # column_filters = [Menu.category] #Menu.status, Menu.is_active
    
    can_create = False
    can_delete = True
    can_edit = True
    can_view_details = True
    
class OrderAdmin(ModelView, model=Order):
    name = "Transaction"
    name_plural = "Transactions"
    icon = "fa-solid fa-receipt"
    
    column_list = [
        Order.id,
        Order.order_id,
        Order.user_id,
        Order.merchant_id,
        Order.total_amount,
        Order.status,
        Order.payment_type,
        Order.created_at,
        Order.paid_at,
    ]
    column_searchable_list = [Order.order_id]
    column_sortable_list = [
        Order.id,
        Order.total_amount,
        Order.status,
        Order.created_at,
        Order.paid_at,
    ]
    # column_filters = [Order.payment_type] #Order.status
    
    can_create = False
    can_delete = False
    can_edit = False
    can_view_details = True

class ReviewAdmin(ModelView, model=Review):
    name = "Review"
    name_plural = "Reviews"
    icon = "fa-solid fa-star"
    
    column_list = [
        Review.id,
        Review.user_id,
        Review.merchant_id,
        Review.rating,
        Review.comment,
        Review.merchant_reply,
        Review.created_at,
    ]
    column_searchable_list = [Review.comment]
    column_sortable_list = [Review.id, Review.rating, Review.created_at]
    # column_filters = [Review.rating]
    
    can_create = False
    can_delete = True # buat delete toxic review 
    can_edit = False
    can_view_details = True