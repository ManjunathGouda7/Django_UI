from playwrightModule import BasePage



BaseObj = BasePage()
BaseObj.setup()
BaseObj.page.locator("//span[text()='Connection Setup']").click()
BaseObj.page.wait_for_timeout(1000)
BaseObj.page.locator("//input[@class='rc-select-search__field']").click()
options = BaseObj.page.locator("//li[@role='option']"+"/option").all_text_contents()
print(options)
BaseObj.page.wait_for_timeout(3000)
# BaseObj.page.locator("//span[text()='QI Specification']/following-sibling::div[1]/button").click()
# BaseObj.page.wait_for_timeout(1000)
# #choose the optionBa
# BaseObj.page.locator("//span[text()='QI Specification']/following-sibling::div[1]/button/following-sibling::div[1]/a[text()='2.3.1']").click()
# BaseObj.page.wait_for_timeout(1000)

# BaseObj.page.locator("//span[text()=' Power Profile ']/following-sibling::div[1]/button").click()
# BaseObj.page.wait_for_timeout(1000)
# BaseObj.page.locator("//span[text()=' Power Profile ']/following-sibling::div[1]/button/following-sibling::div[1]/a[text()='MPP15']").click()
# BaseObj.page.wait_for_timeout(1000)

# with BaseObj.page.expect_request("http://localhost:2004/api/CustomAPIConfiguration_MPPTPT/PutSelectedQiSpecMode_MPP") as req_info,\
#      BaseObj.page.expect_response("http://localhost:2004/api/CustomAPIConfiguration_MPPTPT/PutSelectedQiSpecMode_MPP") as res_info:
#         BaseObj.page.locator("//button[@class='qi-spec-set-button ms-2']").click()

# request = req_info.value
# response = res_info.value

# payload = request.post_data_json
# status = response.status
# print(payload,status)
# BaseObj.page.wait_for_timeout(1000)

BaseObj.teardown()

# Test()