from pkg.plugin.context import register, handler, llm_func, BasePlugin, APIHost, EventContext
from pkg.plugin.events import *  # 导入事件类
from pkg.platform.types import *
import random, re, itertools, json


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
        self.mode = 0 #游戏模式，0为无徽章模式，1为徽章模式
        self.badge_list = [["金制换点徽章", 1], ["金制幸运徽章", 1], ["金制力量徽章", 3], ["金制君主徽章", 0], ["金制先行徽章", 0], ["金制镜像徽章", 3], ["金制重投徽章", 3], ["金制军阀徽章", 1]]
        self.badge_counts = [0, 0]
        try:
            with open(r"plugins/LangBot_Plugin_KCDDiceGame/badge.json", 'r', encoding='utf-8') as f:
                self.player_badges = json.load(f)
        except FileNotFoundError:
            with open(r"plugins/LangBot_Plugin_KCDDiceGame/badge.json", 'w', encoding='utf-8') as f:
                self.player_badges = {}
        pass
        self.wait = -1 #徽章后续操作等待标志，值为等待中的徽章id，-1意味着没有等待
        self.archlord = False #判断是否触发了金制君主徽章

    # 异步初始化
    async def initialize(self):
        pass

    def save_badges(self):
        try:
            with open(r"plugins/LangBot_Plugin_KCDDiceGame/badge.json", 'w', encoding='utf-8') as f:
                json.dump(self.player_badges, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存徽章列表失败：{e}")
    
    def init_badges(self):
        for index, player in enumerate(self.player):
            self.badge_counts[index] = self.badge_list[self.player_badges[str(player)]][1]

    def badge_str(self):
        player_id = self.player[self.turn]
        return f"{player_id} 使用了{self.badge_list[self.player_badges[str(player_id)]][0]}，剩余使用次数为{self.badge_counts[self.turn]}次"

    def dice_calculate(self, dice_ids):
        dices = [0, 0, 0, 0, 0, 0]
        for item in dice_ids:
            dices[self.dice_lake[item - 1] - 1] += 1
        return dices
    
    def score_calculate(self, dices):
        #首先判断金制君主徽章
        if self.mode == 1:
            if dices[0] >= 3 and dices[0] < 6 and self.player_badges[str(self.player[self.turn])] == 3:
                dices[0] -= 3
                self.archlord = True
                return 3000 + self.score_calculate(dices)
        if all(x == 1 for x in dices): #存在1,2,3,4,5,6
            return 1500
        if all(x >= 1 for x in dices[:5]): #存在1,2,3,4,5
            dices = [x - y for x, y in zip(dices, [1, 1, 1, 1, 1, 0])]
            if dices == [0, 0, 0, 0, 0, 0]:
                return 500
            else:
                score_remains = self.score_calculate(dices)
                if score_remains != 0:
                    return 500 + score_remains
                else:
                    return 0
        if all(x >= 1 for x in dices[1:]): # 存在2,3,4,5,6
            dices = [x - y for x, y in zip(dices, [0, 1, 1, 1, 1, 1])]
            if dices == [0, 0, 0, 0, 0, 0]:
                return 750
            else:
                score_remains = self.score_calculate(dices)
                if score_remains != 0:
                    return 750 + score_remains
                else:
                    return 0
        score = 0
        score_rules = {
            1: (100, 1000),
            5: (50, 500),
            2: (0, 200),
            3: (0, 300),
            4: (0, 400),
            6: (0, 600),
        }

        for i, count in enumerate(dices):
            if count >= 1 and i + 1 in score_rules:
                if count <= 2:
                    score += score_rules[i + 1][0] * count
                else:
                    score += score_rules[i + 1][1] * (2 ** (count - 3))
                dices[i] = 0
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
                dices = [0, 0, 0, 0, 0, 0]
                for item in dice_combines:
                    dices[item - 1] += 1
                if self.score_calculate(dices) != 0:
                    return True
        return False
    def build_dice_str(self):
        str = f"第{self.count}次投骰！结果：\n"
        for index, item in enumerate(self.dice_lake):
            str += f"{index + 1}. {item}点\n"
        str += f"\n本回合积分：{self.temp_score} 总积分：{self.score[self.turn]}"
        return str
    def roll_dice(self, dice_ids="", reroll=False):
        if reroll and re.match(fr"^(?!.*(.).*\1)[1-{self.dice_num}]{{1,{self.dice_num}}}$", dice_ids):
            for dice_id in dice_ids:
                self.dice_lake[int(dice_id) - 1] = random.randint(1, 6)
        else:
            self.count += 1
            self.dice_lake = []
            for i in range(self.dice_num):
                self.dice_lake.append(random.randint(1, 6))
        self.wait = -1
        return self.score_check(self.dice_lake)
    def turn_change(self):
        self.count = 0
        self.turn = 1 - self.turn
        self.dice_num = 6
        self.temp_score = 0
        self.wait = -1
        self.archlord = False
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
        self.wait = -1
        self.mode = 0
        self.badge_counts = [0, 0]
        self.archlord = False
    def roll_str(self):
        return f"\n\n现在是 {self.player[self.turn]} 的回合。\n请输入\"投骰\"或\"kcd roll\"进行本回合第一次投骰。"
    # 当收到群消息时触发
    @handler(GroupMessageReceived)
    async def group_message_received(self, ctx: EventContext):
        msg = str(ctx.event.message_chain).strip()  # 这里的 event 即为 GroupNormalMessageReceived 的对象
        sender_id = ctx.event.sender_id
        if msg == "kcd help":
            self.init_game()
            await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain([r"项目地址：https://github.com/Garrise/LangBot_Plugin_KCDDiceGame" + "\n指令列表：\n" +
                                                                                                    "kcd help - 查看指令列表\n" +
                                                                                                    "kcd start [score] / 玩骰子 [分数] - 开始或加入一局骰子游戏，可以自定义目标积分\n" +
                                                                                                    "kcd start badge [score] / 玩徽章骰子 [分数] - 开始一局徽章骰子游戏，可以自定义目标积分\n" +
                                                                                                    "kcd badge / 设定徽章 - 查看当前装备的徽章以及徽章列表\n" +
                                                                                                    "kcd badge [id] / 设定徽章 [序号] - 设定当前装备的徽章\n" +
                                                                                                    "kcd check / 查分 - 查询当前得分\n" +
                                                                                                    "kcd score table / - 查询计分表\n" +
                                                                                                    "kcd reset / 重置骰子游戏 - 重置骰子游戏"]))
            ctx.prevent_default()
        if msg == "重置骰子游戏" or msg =="kcd reset":
            self.init_game()
            await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(["骰子游戏已重置。"]))
            ctx.prevent_default()
        if re.match(r"^玩骰子(?:\s\d+)?$", msg) or re.match(r"^kcd start(?:\s\d+)?$", msg):            
            if self.status == False: #如果游戏尚未开始
                if msg == "玩骰子" or msg == "kcd start": #默认游戏模式
                    self.target_score = 1500
                else:
                    self.target_score = int(msg.split()[-1])
                self.mode = 0
                self.status = True
                self.player[0] = sender_id
                self.dice_lake = []
                self.dice_num = 6
                await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain([f"{sender_id} 发起了一局骰子游戏邀请，目标分为{self.target_score}，回复\"玩骰子\"或\"kcd start\"加入游戏。"]))
                ctx.prevent_default()
            else: #如果游戏已经开始
                if self.player[1] == "":
                    if self.mode == 1 and (not str(sender_id) in self.player_badges):
                        await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain([f"{sender_id} 尚未装备徽章，不能加入徽章骰子游戏。"]))
                        ctx.prevent_default()
                    else:
                        self.player[1] = sender_id
                        self.score = [0, 0]
                        reply = [f"{sender_id} 加入了骰子游戏，游戏开始!\n\n"]
                        if self.mode == 1:
                            #金色先行徽章
                            for index, player in enumerate(self.player):
                                if self.player_badges[str(player)] == 4:
                                    self.score[index] = 1500
                                    reply.append(f"{player} 使用了金制先行徽章，获得1500分！\n\n")
                            #初始化徽章次数
                            self.init_badges()
                        self.turn = random.randint(0, 1)
                        await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain([f"本局游戏由 {self.player[self.turn]} 先攻。\n请输入\"投骰\"或\"kcd roll\"进行本回合第一次投骰。"]))
                        ctx.prevent_default()
                else:
                    await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(["游戏已开始，请等待游戏结束。"]))
                    ctx.prevent_default()

        if re.match(r"^玩徽章骰子(?:\s\d+)?$", msg) or re.match(r"^kcd start badge(?:\s\d+)?$", msg):            
            if self.status == False: #如果游戏尚未开始
                if not str(sender_id) in self.player_badges:
                    await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain([f"{sender_id} 尚未装备徽章，不能发起徽章骰子游戏。"]))
                    ctx.prevent_default()
                else:
                    if msg == "玩徽章骰子" or msg == "kcd start badge": #徽章游戏模式
                        self.target_score = 5000
                    else:
                        self.target_score = int(msg.split()[-1])
                    self.mode = 1
                    self.status = True
                    self.player[0] = sender_id
                    self.dice_lake = []
                    self.dice_num = 6
                    await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain([f"{sender_id} 发起了一局徽章骰子游戏邀请，目标分为{self.target_score}，回复\"玩骰子\"或\"kcd start\"加入游戏。\n要在游戏中使用徽章，请输入\"使用徽章\"或\"kcd use badge\""]))
                    ctx.prevent_default()
            else:
                await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(["游戏已开始，请等待游戏结束。"]))
                ctx.prevent_default()

        if re.match(r"^设定徽章(?:\s\d)?$", msg) or re.match(r"^kcd badge(?:\s\d)?$", msg):
            if msg == "设定徽章" or msg == "kcd badge":
                reply = []
                if str(sender_id) in self.player_badges:
                    reply.append(f"{sender_id} 当前装备了{self.badge_list[self.player_badges[str(sender_id)]][0]}\n\n")
                reply.append("请输入\"设定徽章 [序号]\"或\"kcd badge [id]\"来设定装备的徽章，徽章列表如下：\n" + 
"""1. 金制换点徽章｜投骰后使用，选择任意一颗骰子将其点数更改为１，每局游戏可使用一次
2. 金制幸运徽章｜投骰后使用，可以重投最多三颗骰子，每局游戏可使用一次
3. 金制力量徽章｜投骰前使用，让这次投骰额外增加一颗骰子，每局游戏可使用三次
4. 金制君主徽章｜你的１１１骰子组合获得三倍分数
5. 金制先行徽章｜开局时获得１５００分
6. 金制镜像徽章｜选择骰子前使用，将你所选骰子的分数翻倍，每局游戏可使用三次
7. 金制重投徽章｜投骰后使用，你可以重投所有骰子，每局游戏可使用三次
8. 金制军阀徽章｜跳过回合前使用，将本轮分数翻倍，每局游戏可使用一次
""")
                await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(reply))
                ctx.prevent_default()
            else:
                badge_id = int(msg.split()[-1])
                self.player_badges[str(sender_id)] = badge_id - 1
                self.save_badges() 
                await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain([f"{sender_id} 装备了{self.badge_list[badge_id - 1][0]}"]))
                ctx.prevent_default()

        if re.match(fr"^kcd set [1-6]{{1,{self.dice_num}}}", msg):
            dices = msg[8:]
            for index, item in enumerate(dices):
                self.dice_lake[index] = int(item)
            reply = [self.build_dice_str()]
            reply.append("\n请输入你希望选择的骰子编号，如果你希望继续投骰，请以\"?\"结尾；如果你希望跳过这回合，请以\"!\"结尾。\n例如，如果你希望选择1，2，3号骰子并跳过，则需要输入\"123!\"\n输入\"计分表\"或\"kcd score table\"以查阅计分表。")
            await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(reply))
            ctx.prevent_default()
            
        if (msg == "使用徽章" or msg == "kcd use badge") and self.status == True and self.mode == 1:
            #检查是否轮到使用者
            if sender_id == self.player[self.turn]:
                #检查徽章使用次数
                if self.badge_counts[self.turn] == 0:
                    await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(["徽章使用次数为零！"]))
                    ctx.prevent_default()
                else:
                    #1. 金制换点徽章
                    if self.player_badges[str(sender_id)] == 0:
                        # 检查时点
                        if self.dice_lake != []:
                            self.wait = 0
                            await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(["请输入你要替换的骰子编号。"]))
                            ctx.prevent_default()
                    #2. 金制幸运徽章
                    elif self.player_badges[str(sender_id)] == 1:
                        # 检查时点
                        if self.dice_lake != []:
                            self.wait = 1
                            await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(["请输入你要重投的骰子编号，最多三位数字，例如：\"235\"。"]))
                            ctx.prevent_default()
                    #3. 金制力量徽章
                    elif self.player_badges[str(sender_id)] == 2:
                        if self.wait == 2:
                            await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(["每次投骰只能使用一次！"]))
                            ctx.prevent_default()
                        else:
                            self.wait = 2
                            self.dice_num += 1
                            self.badge_counts[self.turn] -= 1
                            await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(self.badge_str() + f"\n下一次投骰可以增加一个骰子！"))
                            ctx.prevent_default()
                    #6. 金制镜像徽章
                    elif self.player_badges[str(sender_id)] == 5:
                        if self.wait == 5:
                            await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(["每次选择前只能使用一次！"]))
                            ctx.prevent_default()
                        else:
                            self.wait = 5
                            self.badge_counts[self.turn] -= 1
                            await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(self.badge_str() + f"\n这次选择的骰子分数翻倍！"))
                            ctx.prevent_default()
                    #7. 金制重投徽章
                    elif self.player_badges[str(sender_id)] == 6:
                        if self.dice_lake != []:
                            self.badge_counts[self.turn] -= 1
                            success = self.roll_dice()
                            reply = [self.badge_str() + "\n\n" + self.build_dice_str()]
                            if success:
                                reply.append("\n请输入你希望选择的骰子编号，如果你希望继续投骰，请以\"?\"结尾；如果你希望跳过这回合，请以\"!\"结尾。\n例如，如果你希望选择1，2，3号骰子并跳过，则需要输入\"123!\"\n输入\"计分表\"或\"kcd score table\"以查阅计分表。")
                            else:
                                reply.append("\n无法得分，本回合投骰作废！")
                                self.turn_change()
                                reply.append(self.roll_str())
                            await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(reply))
                            ctx.prevent_default()
                    #8. 金制军阀徽章
                    elif self.player_badges[str(sender_id)] == 7:
                        if self.wait == 7:
                            await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(["一回合只能使用一次！"]))
                            ctx.prevent_default()
                        else:
                            self.badge_counts[self.turn] -= 1
                            self.wait = 7
                            await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(self.badge_str() + f"\n本轮分数翻倍！"))
                            ctx.prevent_default()

        #处理徽章后续操作
        #1. 金制换点徽章
        if re.match(r"^[1-6]$", msg) and sender_id == self.player[self.turn] and self.status == True and self.mode == 1 and self.wait == 0:
            self.dice_lake[int(msg) - 1] = 1
            self.badge_counts[self.turn] -= 1
            self.wait = -1
            reply = [self.badge_str() + "\n\n" + self.build_dice_str()]
            reply.append("\n请输入你希望选择的骰子编号，如果你希望继续投骰，请以\"?\"结尾；如果你希望跳过这回合，请以\"!\"结尾。\n例如，如果你希望选择1，2，3号骰子并跳过，则需要输入\"123!\"\n输入\"计分表\"或\"kcd score table\"以查阅计分表。")
            await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(reply))
            ctx.prevent_default()
        #2. 金制幸运徽章
        if re.match(r"^(?!.*(.).*\1)[1-6]{1,3}$", msg) and sender_id == self.player[self.turn] and self.status == True and self.mode == 1 and self.wait == 1:
            success = self.roll_dice(msg, True)
            self.badge_counts[self.turn] -= 1
            self.wait = -1
            reply = [self.badge_str() + "\n\n" + self.build_dice_str()]
            if success:
                reply.append("\n请输入你希望选择的骰子编号，如果你希望继续投骰，请以\"?\"结尾；如果你希望跳过这回合，请以\"!\"结尾。\n例如，如果你希望选择1，2，3号骰子并跳过，则需要输入\"123!\"\n输入\"计分表\"或\"kcd score table\"以查阅计分表。")
            else:
                reply.append("\n无法得分，本回合投骰作废！")
                self.turn_change()
                reply.append(self.roll_str())
            await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(reply))
            ctx.prevent_default()

        if (msg == "投骰" or msg == "kcd roll") and self.player[self.turn] == sender_id and self.status == True: #每回合首次投骰
            success = self.roll_dice()
            reply = [self.build_dice_str()]
            if success:
                reply.append("\n请输入你希望选择的骰子编号，如果你希望继续投骰，请以\"?\"结尾；如果你希望跳过这回合，请以\"!\"结尾。\n例如，如果你希望选择1，2，3号骰子并跳过，则需要输入\"123!\"\n输入\"计分表\"或\"kcd score table\"以查阅计分表。")
            else:
                #检查重投或换点类徽章
                if self.mode == 1 and self.badge_counts[self.turn] > 0 and self.player_badges[str(sender_id)] == 0 or self.player_badges[str(sender_id)] == 1 or self.player_badges[str(sender_id)] == 6:
                    reply.append(f"\n无法得分，你可以使用{self.badge_list[self.player_badges[str(sender_id)]][0]}！不使用请输入\"!\"跳过")
                    self.wait = -2
                else:
                    reply.append("\n无法得分，本回合投骰作废！")
                    self.turn_change()
                    reply.append(self.roll_str())
            await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(reply))
            ctx.prevent_default()

        if msg == "!" and self.wait == -2 and sender_id == self.player[self.turn] and self.status == True:
            reply = ["本回合投骰作废！"]
            self.turn_change()
            reply.append(self.roll_str())
            await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(reply))
            ctx.prevent_default()
        
        if (msg == "查分" or msg == "kcd check") and self.status == True:
            for index, item in enumerate(self.player):
                if item == sender_id:
                    await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain([f"{item} 当前得分为{self.score[index]}"]))
                    ctx.prevent_default()
        
        if msg == "计分表" or msg == "kcd score table":
            await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(["""　规则类型｜　　骰子组合｜分数
————————————————
单骰子得分｜　　　　　１｜１００
　　　　　｜　　　　　５｜５０
————————————————
　顺子得分｜１２３４５６｜１５００
　　　　　｜　１２３４５｜５００
　　　　　｜　２３４５６｜７５０
————————————————
同点数得分｜　　　１１１｜１０００
　　　　　｜　　　２２２｜２００
　　　　　｜　　　３３３｜３００
　　　　　｜　　　４４４｜４００
　　　　　｜　　　５５５｜５００
　　　　　｜　　　６６６｜６００
————————————————
同点数递增｜　　２２２２｜４００
每一个额外｜　２２２２２｜８００
分数翻一倍｜２２２２２２｜１６００"""]))
            ctx.prevent_default()

        if re.match(fr"^(?!.*(.).*\1)[1-{self.dice_num}]{{1,{self.dice_num}}}[!?]$", msg) and self.status == True: #每回合后续算分并投骰
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
                    #金制镜像徽章
                    if self.mode == 1:
                        if self.player_badges[str(sender_id)] == 5 and self.wait == 5:
                            self.temp_score += 2 * score
                            self.wait = -1
                        else:
                            self.temp_score += score
                    else:
                        self.temp_score += score
                    self.dice_num -= len(dice_str)
                    reply = []
                    if self.archlord:
                        self.archlord = False
                        reply.append(f"{sender_id} 触发了金制君主徽章！\n\n")
                    if self.dice_num == 0:
                        self.dice_num = 6
                    if next: #继续投骰
                        success = self.roll_dice()
                        reply.append(self.build_dice_str())
                        if success:
                            reply.append("\n请输入你希望选择的骰子编号，如果你希望继续投骰，请以\"?\"结尾；如果你希望跳过这回合，请以\"!\"结尾。\n例如，如果你希望选择1，2，3号骰子并跳过，则需要输入\"123!\"")
                        else:
                            #检查重投或换点类徽章
                            if self.mode == 1:
                                if self.badge_counts[self.turn] > 0 and self.player_badges[str(sender_id)] == 0 or self.player_badges[str(sender_id)] == 1 or self.player_badges[str(sender_id)] == 6:
                                    reply.append(f"\n无法得分，你可以使用{self.badge_list[self.player_badges[str(sender_id)]][0]}！不使用请输入\"!\"跳过")
                                    self.wait = -2
                                else:
                                    reply.append("\n无法得分，本回合投骰作废！")
                                    self.turn_change()
                                    reply.append(self.roll_str())
                            else:
                                reply.append("\n无法得分，本回合投骰作废！")
                                self.turn_change()
                                reply.append(self.roll_str())
                        await ctx.send_message(ctx.event.launcher_type, str(ctx.event.launcher_id),MessageChain(reply))
                        ctx.prevent_default()
                    else: #跳过投骰，将本回合积分加入总分，切换回合
                        #金制军阀徽章
                        reply = []
                        if self.mode == 1:
                            if self.player_badges[str(sender_id)] == 7 and self.wait == 7:
                                self.score[self.turn] += 2 * self.temp_score
                                reply.append(f"{self.player[self.turn]} 的回合得分为{2 * self.temp_score}分。")
                                self.wait = -1
                            else:
                                self.score[self.turn] += self.temp_score
                                reply.append(f"{self.player[self.turn]} 的回合得分为{self.temp_score}分。")
                        else:
                            self.score[self.turn] += self.temp_score
                            reply.append(f"{self.player[self.turn]} 的回合得分为{self.temp_score}分。")
                        reply.append(f"目前总分为{self.score[self.turn]}。")
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
