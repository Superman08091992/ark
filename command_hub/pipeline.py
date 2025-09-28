from agents.kyle.kyle_agent import KyleAgent
from agents.joey.joey_agent import JoeyAgent
from agents.kenny.kenny_agent import KennyAgent
from core.hrm.hrm import HRM
from core.aletheia.aletheia import Aletheia
from core.telegram_bot import TelegramBot

class ARKPipeline:
    def __init__(self):
        self.kyle=KyleAgent(); self.joey=JoeyAgent(); self.kenny=KennyAgent()
        self.hrm=HRM(); self.aletheia=Aletheia(); self.telegram=TelegramBot()

    def run(self,req:str):
        self.telegram.send_alert("Pipeline start: "+req)
        package=self.kyle.package_for_joey(req)
        plan=self.joey.analyze_and_plan(package)
        if not self.hrm.validate(plan): raise Exception("HRM failed")
        if not self.aletheia.enforce_ethics(plan): raise Exception("Ethics failed")
        res=self.kenny.execute(plan,True)
        self.telegram.send_alert("Execution completed")
        return res
