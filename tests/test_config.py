from config.site_config import SauceDemoConfig


def test_site_config_supports_generic_shop_interface():
    config = SauceDemoConfig()

    assert config.base_url == "https://www.saucedemo.com/"
    assert config.users["standard_user"]["username"] == "standard_user"
    assert config.selectors["login"]["username_placeholder"] == "Username"
    assert config.selectors["products"]["inventory_item_name"] == ".inventory_item_name"
