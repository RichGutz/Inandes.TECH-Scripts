try:
    import selenium
    print("Selenium is installed")
except ImportError:
    print("Selenium is NOT installed")

try:
    import webdriver_manager
    print("webdriver_manager is installed")
except ImportError:
    print("webdriver_manager is NOT installed")