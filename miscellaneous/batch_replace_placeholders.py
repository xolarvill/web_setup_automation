from selenium import webdriver
from selenium.webdriver.common.by import By

"""
使用selenium创建bot批量替换图片占位符
自动化程度：全自动 + 人工监督
"""

driver = webdriver.Chrome()

search_input = driver.find_element(By.Xpath, """//input[@id='input-138']""")

search_button = driver.find_element(By.Xpath, """//div[@id='app']/div[@class='v-application--wrap']/main[@class='v-main content']/div[@class='v-main__wrap']/div[@class='container container--fluid']/div[@class='tables-basic']/div[@class='row']/div[@class='col col-12'][1]/div[@class='employee-list pa-4 v-card v-sheet theme--light']/div[@class='row']/div[@class='col-sm-12 col-md-8 col-lg-3 col-12']/button[@class='ml-4 v-btn v-btn--is-elevated v-btn--has-bg theme--light v-size--large primary']""")

edit_button = driver.find_element(By.Xpath, """//div[@id='app']/div[@class='v-application--wrap']/main[@class='v-main content']/div[@class='v-main__wrap']/div[@class='container container--fluid']/div[@class='tables-basic']/div[@class='row']/div[@class='col col-12'][2]/div[@class='employee-list pa-4 v-card v-sheet theme--light']/div[@class='v-data-table theme--light']/div[@class='v-data-table__wrapper']/table/tbody/tr/td[@class='table-td'][11]/div/button[@class='v-btn v-btn--icon v-btn--round theme--dark v-size--default primary--text']/span[@class='v-btn__content']/i[@class='v-icon notranslate mdi mdi-dots-horizontal theme--dark']""")

open_edit_page = driver.find_element(By.XPATH,"""//div[@id='app']/div[@class='v-menu__content theme--light menuable__content__active']/div[@class='mx-auto v-card v-sheet theme--light rounded-0']/div[@class='v-list v-sheet theme--light v-list--dense']/div[@class='v-item-group theme--light v-list-item-group primary--text']/div[@class='v-list-item v-list-item--link theme--light'][1]/div[@class='v-list-item__content']/div[@class='v-list-item__title']""")

open_pop_up_editor = driver.find_element(By.XPATH,"""//div[@id='app']/div[@class='v-application--wrap']/main[@class='v-main content']/div[@class='v-main__wrap']/div/div[@class='col col-12']/div[@class='employee-list pa-12 v-card v-sheet theme--light']/div[16]/div[@class='insert']/div[@class='inset-content']/div[@class='row']/div[@class='col col-4']/button[@class='v-btn v-btn--is-elevated v-btn--has-bg v-btn--rounded theme--light v-size--default primary']/span[@class='v-btn__content']""")

json_tool = driver.find_element(By.XPATH,"""//div[@id='app']/div[@class='app-root']/div[@class='app-header']/div[@class='header-root']/div[@class='tools']/button[@class='el-button el-button--primary is-round'][1]/span""")

get_json = driver.find_element(By.XPATH,"""//div[@id='el-id-6100-1']/div[1]/button[@class='el-button is-round']/span""")

# 替换图片相关CDN

json_input = driver.find_element(By.XPATH,"""//textarea[@id='el-id-6100-86']""")

json_input_save = driver.find_element(By.XPATH,"""//div[@id='el-id-6100-1']/button[@class='el-button']/span""")

save_pop_up_editor = driver.find_element(By.XPATH,"""//div[@id='app']/div[@class='app-root']/div[@class='app-header']/div[@class='header-root']/div[@class='tools']/button[@class='el-button el-button--primary is-round'][3]/span""")

save_edit_page = driver.find_element(By.XPATH,"""//div[@id='app']/div[@class='v-application--wrap']/main[@class='v-main content']/div[@class='v-main__wrap']/div/div[3]/div[@class='btn-box']/button[@class='v-btn v-btn--is-elevated v-btn--has-bg theme--light v-size--default primary']/span[@class='v-btn__content']""")