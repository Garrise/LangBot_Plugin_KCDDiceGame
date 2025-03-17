from pkg.plugin.context import register, handler, llm_func, BasePlugin, APIHost, EventContext
from pkg.plugin.events import *  # 导入事件类
from pkg.platform.types import *
import random, re, itertools


# 注册插件
@register(name="KCD Dice Game", description="Play dice game of KCD", version="0.1", author="Garrise")
class KCDDiceGamePlugin(BasePlugin):

    # 插件加载时触发
    def __init__(self, host: APIHost):
        self.status = False
        self.player = ["",""]
        self.score = [0, 0]
        self.turn = 0
        self.dice_lake = []
        self.dice_num = 6
        self.count = 0
        self.temp_score = 0
        self.target_score = 1500
        pass

    # 异步初始化
    async def initialize(self):
        pass

    def dice_calculate(self, dice_ids):
        dices = [0, 0, 0, 0, 0, 0]
        for item in dice_ids:
            dices[self.dice_lake[item - 1] - 1] += 1
        return dices
    
    def score_calculate(self, dices):
        if all(x == 1 for x in dices): #存在1,2,3,4,5,6
            return 1500
        elif all(x >= 1 for x in dices[:5]): #存在1,2,3,4,5
            dice_remains = [x - y for x, y in zip(dices, [1, 1, 1, 1, 1, 0])]
            if dice_remains == [0, 0, 0, 0, 0, 0]:
                return 500
            else:
                score_remains = self.score_calculate(dice_remains)
                if score_remains != 0:
                    return 500 + score_remains
                else:
                    return 0
        elif all(x >= 1 for x in dices[1:]): # 存在2,3,4,5,6
            dice_remains = [x - y for x, y in zip(dices, [0, 1, 1, 1, 1, 1])]
            if dice_remains == [0, 0, 0, 0, 0, 0]:
                return 750
            else:
                score_remains = self.score_calculate(dice_remains)
                if score_remains != 0:
                    return 750 + score_remains
                else:
                    return 0
        elif dices[0] >= 1: #存在1
            score = 0
            if dices[0] <= 2:
                score += 100 * dices[0]
            else:
                score += 1000 * (2 ** (dices[0]-3))
            dices[0] = 0
            if dices == [0, 0, 0, 0, 0, 0]:
                return score
            else:
                score_remains = self.score_calculate(dices)
                if score_remains != 0:
                    return score + score_remains
                else:
                    return 0
        elif dices[1] >= 1: #存在2
            score = 0
            if dices[1] >= 3:
                score += 200 * (2 ** (dices[1]-3))
            dices[1] = 0
            if dices == [0, 0, 0, 0, 0, 0]:
                return score
            else:
                score_remains = self.score_calculate(dices)
                if score_remains != 0:
                    return score + score_remains
                else:
                    return 0
        elif dices[2] >= 1: #存在3
            score = 0
            if dices[2] >= 3:
                score += 300 * (2 ** (dices[2]-3))
            dices[2] = 0
            if dices == [0, 0, 0, 0, 0, 0]:
                return score
            else:
                score_remains = self.score_calculate(dices)
                if score_remains != 0:
                    return score + score_remains
                else:
                    return 0
        elif dices[3] >= 1: #存在4
            score = 0
            if dices[3] >= 3:
                score += 400 * (2 ** (dices[3]-3))
            dices[3] = 0
            if dices == [0, 0, 0, 0, 0, 0]:
                return score
            else:
                score_remains = self.score_calculate(dices)
                if score_remains != 0:
                    return score + score_remains
                else:
                    return 0
        elif dices[4] >= 1: #存在5
            score = 0
            if dices[4] <= 2:
                score += 50 * dices[4]
            else:
                score += 500 * (2 ** (dices[4]-3))
            dices[4] = 0
            if dices == [0, 0, 0, 0, 0, 0]:
                return score
            else:
                score_remains = self.score_calculate(dices)
                if score_remains != 0:
                    return score + score_remains
                else:
                    return 0
        elif dices[5] >= 1: #存在6
            score = 0
            if dices[5] >= 3:
                score += 600 * (2 ** (dices[5]-3))
            dices[5] = 0
            if dices == [0, 0, 0, 0, 0, 0]:
                return score
            else:
                score_remains = self.score_calculate(dices)
                if score_remains != 0:
                    return score + score_remains
                else:
                    return 0
        return 0
    def score_check(self, dice_lake):
        dices = [0, 0, 0, 0, 0, 0]
        for i in range(1, 6):
            for dice_combines in itertools.combinations(dice_lake, i):
                for item in dice_combines:
                    dices[item - 1] += 1
                if self.score_calculate(dices) != 0:
                    return True
        return False
    def build_dice_str(self):
        str = f"第{self.count}次投骰！结果：\n"
        for index, item in enumerate(self.dice_lake):
            str += f"{index + 1}. {item}点\n"
        str += f"\n本回合积分：{self.temp_score}"
        return str
    def roll_dice(self):
        self.count += 1
        self.dice_lake = []
        for i in range(self.dice_num):
            self.dice_lake.append(random.randint(1, 6))
        return self.score_check(self.dice_lake)
    def turn_change(self):
        self.count = 0
        self.turn = 1 - self.turn
        self.dice_num = 6
        self.temp_score = 0
    def init_game(self):
        self.status = False
        self.player = ["",""]
        self.score = [0, 0]
        self.turn = 0
        self.dice_lake = []
        self.dice_num = 6
        self.count = 0
        self.temp_score = 0
        self.target_score = 1500
    def roll_str(self):
        return f"\n\n现在是 {self.player[self.turn]} 的回合。\n请输入\"投骰\"或\"kcd roll\"进行本回合第一次投骰。"
    # 当收到群消息时触发
    @handler(GroupMessageReceived)
    async def group_message_received(self, ctx: EventContext):
        msg = str(ctx.event.message_chain).strip()  # 这里的 event 即为 GroupNormalMessageReceived 的对象
        sender_id = ctx.event.sender_id
        if msg == "重置骰子游戏" or msg =="kcd reset":
            self.init_game()
            await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(["游戏已重置。"]))
            ctx.prevent_default()
        if msg == "玩骰子" or msg == "kcd start":  # 如果消息为玩骰子
            
            if self.status == False: #如果游戏尚未开始
                self.status = True
                self.player[0] = sender_id
                self.dice_lake = []
                self.dice_num = 6
                # 输出调试信息
                self.ap.logger.debug("开始一局骰子游戏，邀请其他人参加, {}".format(ctx.event.sender_id))
                await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain([f"{sender_id} 发起了一局骰子游戏邀请，回复\"玩骰子\"或\"kcd start\"加入游戏。"]))
                ctx.prevent_default()
            else: #如果游戏已经开始
                if self.player[1] == "":
                    self.player[1] = sender_id
                    self.score = [0, 0]
                    self.turn = random.randint(0, 1)
                    await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain([f"{sender_id} 加入了骰子游戏，游戏开始!\n本局游戏由 {self.player[self.turn]} 先攻。\n请输入\"投骰\"或\"kcd roll\"进行本回合第一次投骰。"]))
                    ctx.prevent_default()
                else:
                    await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(["游戏已开始，请等待游戏结束。"]))
                    ctx.prevent_default()

        if (msg == "投骰" or msg == "kcd roll") and self.player[self.turn] == sender_id: #每回合首次投骰
            success = self.roll_dice()
            reply = [self.build_dice_str()]
            if success:
                reply.append("\n请输入你希望选择的骰子编号，如果你希望继续投骰，请以\"?\"结尾；如果你希望跳过这回合，请以\"!\"结尾。\n例如，如果你希望选择1，2，3号骰子并跳过，则需要输入\"123!\"\n输入\"计分表\"或\"kcd score table\"以查阅计分表。")
            else:
                reply.append("\n无法得分，本回合投骰作废！")
                self.turn_change()
                reply.append(self.roll_str())
            await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(reply))
            ctx.prevent_default()
        
        if msg == "查分" or msg == "kcd check":
            for index, item in enumerate(self.player):
                if item == sender_id:
                    await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain([f"{item} 当前得分为{self.score[index]}"]))
                    ctx.prevent_default()
        
        if msg == "计分表" or msg == "kcd score table":
            await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(["每个1计100分\n每个5计50分\n1 2 3 4 5的顺子计500分\n2 3 4 5 6的顺子计750分\n1 2 3 4 5 6的顺子计1500分\n\n三个1计1000分\n三个2计200分\n三个3计300分\n三个4计400分\n三个5计500分\n三个6计600分\n三个骰子后每增加一个骰子，分数翻倍，例如：\n4个2计400分，5个2计800分，6个2计1600分"]))
            ctx.prevent_default()

        if re.match(r"^(?!.*(.).*\1)[1-6]{1,6}[!?]$", msg): #每回合后续算分并投骰
            if self.player[self.turn] == sender_id:
                dice_ids = []
                next = False
                if msg[-1] == "!":
                    next = False
                elif msg[-1] == "?":
                    next = True
                dice_str = msg[:-1]
                for char in dice_str:
                    dice_ids.append(int(char))
                score = self.score_calculate(self.dice_calculate(dice_ids))
                if score == 0:
                    await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(["分数为零，请重新选择。"]))
                    ctx.prevent_default()
                else: #算分有效，计入本回合积分，去除使用过的骰子，并判断是否继续投骰
                    self.temp_score += score
                    self.dice_num -= len(dice_str)
                    if self.dice_num == 0:
                        self.dice_num = 6
                    if next: #继续投骰
                        success = self.roll_dice()
                        reply = [self.build_dice_str()]
                        if success:
                            reply.append("\n请输入你希望选择的骰子编号，如果你希望继续投骰，请以\"?\"结尾；如果你希望跳过这回合，请以\"!\"结尾。\n例如，如果你希望选择1，2，3号骰子并跳过，则需要输入\"123!\"")
                        else:
                            reply.append("\n无法得分，本回合投骰作废！")
                            self.turn_change()
                            reply.append(self.roll_str())
                        await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(reply))
                        ctx.prevent_default()
                    else: #跳过投骰，将本回合积分加入总分，切换回合
                        self.score[self.turn] += self.temp_score
                        reply = [f"{self.player[self.turn]} 的回合得分为{self.temp_score}分。目前总分为{self.score[self.turn]}。"]
                        if self.score[self.turn] >= self.target_score:
                            reply.append(f"{self.player[self.turn]} 赢得了胜利！")
                            self.init_game()
                        else:
                            self.turn_change()
                            reply.append(self.roll_str())
                        await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(reply))
                        ctx.prevent_default


    # 插件卸载时触发
    def __del__(self):
        pass
