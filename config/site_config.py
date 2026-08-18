from __future__ import annotations


class BaseStoreConfig:
    """Generic configuration contract for e-commerce QA flows."""

    name: str = "generic_store"
    base_url: str = "https://example.com/"
    users: dict[str, dict[str, str]] = {}
    customers: dict[str, dict[str, str]] = {}
    products: dict[str, str] = {}
    selectors: dict[str, dict[str, str]] = {}


class SauceDemoConfig(BaseStoreConfig):
    name = "saucedemo"
    base_url = "https://www.saucedemo.com/"
    users = {
        "standard_user": {"username": "standard_user", "password": "secret_sauce"},
        "locked_out_user": {"username": "locked_out_user", "password": "secret_sauce"},
    }
    customers = {
        "default": {"first_name": "Ada", "last_name": "Lovelace", "postal_code": "12345"},
    }
    products = {
        "backpack": "Sauce Labs Backpack",
        "bike_light": "Sauce Labs Bike Light",
        "bolt_tshirt": "Sauce Labs Bolt T-Shirt",
    }
    selectors = {
        "login": {
            "username_placeholder": "Username",
            "password_placeholder": "Password",
            "submit_button": "Login",
            "error": "[data-test='error']",
        },
        "products": {
            "title": "Products",
            "inventory_item": ".inventory_item",
            "inventory_item_name": ".inventory_item_name",
            "inventory_item_price": ".inventory_item_price",
            "sort_container": "[data-test='product-sort-container']",
            "cart_badge": "[data-test='shopping-cart-badge']",
            "shopping_cart_link": "[data-test='shopping-cart-link']",
            "product_button": "Add to cart",
        },
        "cart": {
            "item": ".cart_item",
            "checkout_button": "Checkout",
            "continue_button": "Continue Shopping",
            "remove_button": "Remove",
        },
        "checkout": {
            "first_name_input": "[data-test='firstName']",
            "last_name_input": "[data-test='lastName']",
            "postal_code_input": "[data-test='postalCode']",
            "continue_button": "Continue",
            "finish_button": "Finish",
            "total_label": ".summary_total_label",
            "error": "[data-test='error']",
            "success_message": "Thank you for your order!",
        },
    }


DEFAULT_CONFIG = SauceDemoConfig()
