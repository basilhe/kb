import time
import pywinauto
import pyautogui
from pywinauto import application
from services import yolo
import time
import io

"""
keyword: https://pywinauto.readthedocs.io/en/latest/code/pywinauto.keyboard.html?highlight=send_keys#pywinauto-keyboard
"""
class HCaptchaResolver():
    yolo_model = None
    
    def __init__(self, security_doc, challenge_doc):
        self.security_doc = security_doc
        self.challenge_doc = challenge_doc
    
    def get_yolo_model(self):
        if self.yolo_model is None:
            self.yolo_model = yolo.YOLO('model', onnx_prefix='yolov5n6') #model: Default "yolov5s6". within [yolov5n6 yolov5s6 yolov5m6 yolov6n yolov6t yolov6s
        return self.yolo_model
    
    def match_image(self, image, label):
        return self.get_yolo_model().solution(img_stream=image, label=label)
    
    def image_to_byte_array(self, pil_image):
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()
        
    def resolve(self, dsb):
        btn_start = self.security_doc.child_window(control_type="CheckBox")
        if btn_start.wait('visible', timeout=60):
            
            btn_start.click()
            
            time.sleep(1)
            
            header = self.challenge_doc.child_window(title="挑战图片1", control_type="Button")
            header.wait('visible')
            
            submit = self.challenge_doc.child_window(title="跳过挑战", control_type="Button")
            next = self.challenge_doc.child_window(title="下一个挑战", control_type="Button")
            check = self.challenge_doc.child_window(title="提交答案", control_type="Button")
            while True:
                title = dsb.dsb_win.Document.window_text()
                if '一条船' in title:
                    label = 'boat'
                elif '公交车' in title:
                    label = 'bus'
                elif '飞机' in title:
                    label = 'airplane'
                else:
                    return
                
                for x in range(1, 10):
                    btn_img = self.challenge_doc.child_window(title=u"挑战图片%d" % x, control_type="Button")
                    img = btn_img.capture_as_image()

                    if self.match_image(self.image_to_byte_array(img), label):
                        btn_img.click()
                    # img.save("d:/ebay-control/challenge/image-%d.png" % x)
                
                # self.challenge_doc.child_window(title="Refresh Challenge.", control_type="Button")
                try:
                    next.wait('visible', timeout=0.1)
                    next.click()
                except:
                    try:
                        check.wait('visible', timeout=0.1)
                        check.click()
                    except:
                        try:
                            check.wait('visible', timeout=0.1)
                            submit.click()
                        except:
                            break
                time.sleep(1.5)
             # child_window(title="跳过", control_type="Text")
        
class DsbBrowser():
    def __init__(self, account_name: str):
        self.account_name = account_name
        self.dsb_app = application.Application(backend='uia').connect(title_re='%s | eBay.*' % account_name, timeout=20)
        self.dsb_win = self.dsb_app.window(title_re='%s | eBay.*' % account_name, control_type='Pane')
        self.dsb_win.wait('exists', 5)

        self.titlebar = self.dsb_win.TitleBar
        self.address_edit = self.titlebar.child_window(title=u"地址和搜索栏", control_type="Edit")
        self.btn_refresh = self.titlebar.child_window(title=u"重新加载", control_type="Button")
        self.btn_stop = self.titlebar.child_window(title=u"停止加载", control_type="Button")

        self.lang = self.dsb_win.texts()[0].split('|')[1].strip()[-2:]
        
    def get_url(self):
        return self.address_edit.get_value()
    
    def get_document(self):
        doc = self.dsb_win.Document
        while len(doc.window_text()) == 0:
            time.sleep(1)
        self.btn_refresh.wait('visible', 10)
        return doc
    
    def get_captcha_security_document(self):
        doc = self.dsb_win.Document
        pane = doc.child_window(title="widget containing checkbox for hCaptcha security challenge", control_type="Pane")
        captcha = pane.child_window(title="hCaptcha", control_type="Document")
        return captcha
    def get_captcha_challenge_document(self):
        doc = self.dsb_win.Document
        pane = doc.child_window(title="Main content of the hCaptcha challenge", control_type="Pane")
        captcha = pane.child_window(title="hCaptcha", control_type="Document")
        return captcha 
    
    def hcaptcha_challenger(self):
        return HCaptchaResolver(self.get_captcha_security_document(), self.get_captcha_challenge_document())   
    
    def close(self):
        while True:
            self.dsb_win.type_keys('%{F4}')
            try:
                self.dsb_win.wait_not('exists', timeout=5)
                break
            except:
                btn_continue = self.dsb_win.child_window(title=u"继续下载", control_type="Button")
                btn_continue.click()

    def open_url(self, url):
        self.address_edit.type_keys('^a%s{ENTER}' % url)
        self.btn_refresh.wait('ready', 3)

    def traffic_download(self):
        btn_download = self.dsb_win.Document.child_window(title=self.i18n('traffic_report'), control_type='Button')
        btn_download.wait('ready', 60)
        btn_download.invoke()
        self.save_traffic_as()
        time.sleep(5)
        
    def refresh_page(self):
        self.btn_refresh.click()
        
    def save_traffic_as(self):
        dlg = self.dsb_win.child_window(title=u"另存为", control_type="Window") #, class_name="#32770"
        btn_save = dlg.child_window(title_re='保存.*', control_type="Button")
        try:
            if dlg.wait('exists', 60):
                btn_save.click()
        except Error as e:
            print("failed to download: %s", e)
            pass
    def try_signin(self) -> bool:
        btn_signin_continue = self.dsb_win.Document.child_window(auto_id="signin-continue-btn", control_type="Button")
        try:
            btn_signin_continue.wait('enabled', 0.1)
            btn_signin_continue.click()
            return True
        except:
            pass
        
        btn_signin = self.dsb_win.Document.child_window(auto_id="sgnBt", control_type="Button")
        try:
            btn_signin.wait('enabled', 0.1)
            btn_signin.click()
            return True
        except:
            pass

        return False
    
    def try_accept_cookies(self):
        btn_accept_cookies = self.dsb_win.Document.child_window(auto_id="gdpr-banner-accept", control_type="Button")
        try:
            btn_accept_cookies.wait('enabled', 0.1)
            btn_accept_cookies.click()
        except:
            pass
    
    _i18n_texts = {
        'traffic_report': {
            'FR': u'Télécharger le rapport sur le taux de fréquentation des annonces en cours',
            'DE': u"Traffic-Bericht zu aktiven Angeboten herunterladen",
            'UK': "Download active listings traffic report",
            'US': "Download active listings traffic report",
            'AU': "Download active listings traffic report",
            'IT': "Download active listings traffic report",
        }
    }
    def i18n(self, key):
        if key in self._i18n_texts:
            return self._i18n_texts[key][self.lang]
    
class DsbConsole():
    def __init__(self):
        self.dsc_app = application.Application(backend='uia').connect(title_re=u".*电商浏览器", timeout=20)
        self.dsc_app.top_window().set_focus()
        
        self.dsc_win = self.dsc_app.window(title=u'电商浏览器', control_type='Pane')
        self.search_input = self.dsc_win.child_window(title=u'店铺简称/用户名/通道名称/通道IP/标签', control_type='Edit')

    def open_browser(self, account_name: str) -> DsbBrowser:
        self.dsc_app.top_window().set_focus()
        self.search_input.type_keys('^a%s{ENTER}' % account_name)
        time.sleep(0.2)
        
        btn_enter = self.dsc_win.child_window(title="进入", control_type="Hyperlink")
        try:
            btn_enter.wait('enabled', 3)
            btn_enter.invoke()
            return DsbBrowser(account_name)
        except pywinauto.timings.TimeoutError as e:
            raise e
        

# dsb_win.print_control_identifiers()

def download_traffic():
    dsc = DsbConsole()
    accounts = [
        'Bestseller_6', 
        'cycletool', 
        'gartenshop-20', 
        'love_fashion_it', 
        'mmfashiontrends', 
        'Wonderparthome_US']

    for account_name in accounts:
        dsb = dsc.open_browser(account_name)
        
        while True:
            dsb.get_document()
            url = dsb.get_url()
            print(url)
            dsb.try_accept_cookies()
            if 'accountsettings' in url:
                print('accountsettings')
                traffic_url = '/'.join(url.split('/')[0:3] + ['sh/performance/traffic']).replace('accountsettings', 'www')
                dsb.open_url(traffic_url)
            elif 'captcha' in url:
                print('hCaptcha')
                captcha_resolver = dsb.hcaptcha_challenger()
                try:
                    captcha_resolver.resolve(dsb)
                except:
                    pass
            elif 'signin' in url:
                print('signin')
                if not dsb.try_signin():
                    print('hCaptcha in signin')
                    captcha_resolver = dsb.hcaptcha_challenger()
                    try:
                        captcha_resolver.resolve(dsb)
                    except:
                        pass
            elif 'sh/performance/traffic' in url:
                print('traffic')
                try:
                    dsb.traffic_download()
                    break
                except:
                    dsb.refresh_page()
            else:
                print('other')
                traffic_url = '/'.join(url.split('/')[0:3] + ['sh/performance/traffic'])
                dsb.open_url(traffic_url)
                
        # time.sleep(5)
        dsb.close()
    
if __name__ == '__main__':
    test = False
    
    if test:
        dsb = DsbBrowser('mmfashiontrends')
        dsb.dsb_app.top_window().set_focus()
        # btn = dsb.dsb_win.Document.child_window(title=u'Télécharger le rapport sur le taux de fréquentation des annonces en cours', control_type='Button')
        # btn.print_control_identifiers()
        dsb.refresh_page()
        # dsb.try_accept_cookies()
        # dsb.try_signin()
        # captcha = dsb.get_captcha_challenge_document()
        # captcha.print_control_identifiers()
        # resolver = HCaptchaResolver(dsb.get_captcha_security_document(), dsb.get_captcha_challenge_document())
        # resolver.resolve(dsb)
        pass
    else:
        download_traffic()
