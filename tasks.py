from robocorp.tasks import task
from RPA.HTTP import HTTP
from RPA.PDF import PDF
from RPA.Archive import Archive

#from playwright.sync_api import sync_playwright
from robocorp import browser
import csv 
import os

os.makedirs("output", exist_ok=True)
os.makedirs("output/receipts", exist_ok=True)

# show model info
MAPPING_TABLE = {
    "1": "Roll-a-thor",
    "2": "Peanut crusher",
    "3": "D.A.V.E",
    "4": "Andy Roid",
    "5": "Spanner mate",
    "6": "Drillbit 2000"
}

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    # with sync_playwright() as playwright:
    #     chromium = playwright.chromium  # or "firefox" or "webkit".
    #     browser = chromium.launch(headless=False)
    #     page = browser.new_page()
    #     page.goto("https://robotsparebinindustries.com/#/robot-order")
    #     download_order_file()
    #     close_annoying_modal(page)
    #     process_orders_from_csv(page)
    #     archive_receipts()

    browser.configure(slowmo=10)
    open_order_robot_website()
    download_order_file()
    close_annoying_modal()
    process_orders_from_csv()
    archive_receipts()

# for playwright reference for future usage
# def process_orders_from_csv(page):
#     """
#     Fills the form with data from the CSV file and clicks 'Order' for each row.
#     """
#     with open("orders.csv", mode="r", newline="", encoding="utf-8") as csvfile:
#         reader = csv.DictReader(csvfile)
#         for row in reader:
#             order_number = fill_robot_order_form(row, page)
#             print("order_number: ", order_number)
#             click_order(order_number, page)
#     #return order_number
#     #print("order_number: ", order_number)

def open_order_robot_website():
    browser.goto("https://robotsparebinindustries.com/#/robot-order")

def download_order_file():
    """
    Downloads the order file from the RobotSpareBin Industries Inc.
    """
    http = HTTP()
    http.download(url="https://robotsparebinindustries.com/orders.csv", overwrite=True)

def process_orders_from_csv():
    """
    Fills the form with data from the CSV file and clicks 'Order' for each row.
    """
    with open("orders.csv", mode="r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            order_number = fill_robot_order_form(row)
            print("order_number: ", order_number)
            click_order(order_number)
    #return order_number
    #print("order_number: ", order_number)

def fill_robot_order_form(row):
    """
    Fills the robot order form and submits it.
    """
    page = browser.page()
    print("Raw row data:", row)

    head_label = MAPPING_TABLE.get(row["Head"], row["Head"])  
    body_value = MAPPING_TABLE.get(row["Body"], row["Body"])

    print("Mapped head_label:", head_label)
    print("Mapped body_value:", body_value)

    page.select_option("#head", label=head_label + " head")

    body_text = f"{body_value} body"
    radio_buttons = page.locator("input.form-check-input[name='body']").all()
    for radio in radio_buttons:
        label = radio.locator("xpath=..").inner_text()
        if body_text in label:
            radio.check()
            break

    page.fill("input[placeholder='Enter the part number for the legs']", row["Legs"])
    page.fill("#address", row["Address"])

    order_number =  row['Order number']
    return order_number

def close_annoying_modal():
    """
    Closes the annoying modal that appears.
    """
    page = browser.page()
    page.click("text=I guess so...")


def click_order(order_number):
    """
    Clicks the 'Order' button and retries until a confirmation message is visible.
    """
    page = browser.page()
    while True:
        page.wait_for_selector("text=Order", state="visible")
        page.click("#order")
        
        confirmation_message = page.locator("div.alert-success")
        error_message = page.locator("div.alert-danger")
        
        if confirmation_message.is_visible():
            print("Order placed successfully!")
            screenshot_path = screenshot_robot(order_number)
            receipt_path = store_receipt_as_pdf(order_number)
            page.click("#order-another")
            close_annoying_modal()
            embed_screenshot_to_receipt(screenshot_path, receipt_path)
            return
        elif error_message.is_visible():
            print("Error placing the order. Retrying...")
        else:
            print("No confirmation or error message detected. Retrying...")

def screenshot_robot(order_number):
    page = browser.page()
    robot_preview_html = page.locator("#robot-preview-image")
    robot_preview_html.wait_for(state="visible", timeout=10000)

    os.makedirs("output/receipts/images", exist_ok=True)
    screenshot_path = f"output/receipts/images/{order_number}_robot_preview.png"
    robot_preview_html.screenshot(path=f"output/receipts/images/{order_number}_robot_preview.png")

    return screenshot_path



def store_receipt_as_pdf(order_number):
    page = browser.page()
    store_receipt_html = page.locator("#receipt").inner_html()

    pdf = PDF()
    receipt_path = f"output/receipts/{order_number}_store_receipt.pdf"
    pdf.html_to_pdf(store_receipt_html, f"output/receipts/{order_number}_store_receipt.pdf")
    return receipt_path

def embed_screenshot_to_receipt(screenshot, pdf_file):
    """
    Embeds the screenshot into the PDF receipt.
    """
    pdf = PDF()
    pdf.open_pdf(pdf_file)
    pdf.add_watermark_image_to_pdf(screenshot, pdf_file)
    pdf.save_pdf(pdf_file)

def archive_receipts():
    lib = Archive()
    lib.archive_folder_with_zip('./output/receipts', 'output/receipts.zip', recursive=True) # recursive: should sub directories be included, default is False