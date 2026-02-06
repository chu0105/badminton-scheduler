import json
import random
import os
import itertools

class BadmintonApp:
    def __init__(self, folder_path="BADMINTON", data_file="players.json"):
        # 取得目前腳本所在的絕對路徑，確保讀取到正確的 players.json
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.data_file = os.path.join(self.base_path, data_file)
        self.players = self.load_data()

    def load_data(self):
        """讀取球員 JSON 資料"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def save_data(self):
        """儲存球員資料至 JSON 檔案"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.players, f, ensure_ascii=False, indent=4)

    def add_player(self, name, level, gender='M'):
        """新增球員，若已存在則跳過"""
        for p in self.players:
            if p['name'] == name: return
        self.players.append({
            "name": name, 
            "level": level, 
            "gender": gender,
            "play_count": 0, 
            "wait_round": 0, 
            "partners_history": []
        })
        self.save_data()

    def _get_best_match_combination(self, four_players):
        """
        核心演算法：在選定的 4 人中找出實力最平均的對戰組合。
        """
        best_match = None
        min_score = float('inf')
        
        # 從 4 人中選 2 人作為一隊的組合共有 3 種 (3=C(4,2)/2)
        for team1_indices in itertools.combinations(range(4), 2):
            team2_indices = [idx for idx in range(4) if idx not in team1_indices]
            t1 = [four_players[i] for i in team1_indices]
            t2 = [four_players[i] for i in team2_indices]
            
            # 計算實力總和差距
            diff = abs(sum(p['level'] for p in t1) - sum(p['level'] for p in t2))
            
            # 性別獎勵：若能組成混雙 vs 混雙，則給予獎勵分降低 Score
            gender_bonus = 0
            t1_females = sum(1 for p in t1 if p['gender'] == 'F')
            t2_females = sum(1 for p in t2 if p['gender'] == 'F')
            if t1_females == 1 and t2_females == 1:
                gender_bonus = -1 
                
            total_score = diff + gender_bonus
            
            if total_score < min_score:
                min_score = total_score
                best_match = (t1, t2)
        
        return best_match

    def get_scheduled_matches(self, active_names, num_courts=None):
        """
        初始排程：一次產生所有場地的對戰名單。
        """
        active_players = [p for p in self.players if p['name'] in active_names]
        if not num_courts:
            num_courts = len(active_players) // 4
        
        if num_courts == 0: return 0, []

        # 排序邏輯：等待回合權重 > 已上場次數
        active_players.sort(key=lambda x: (x['wait_round'] * 15 - x['play_count']), reverse=True)
        on_court_pool = active_players[:num_courts * 4]
        off_court_pool = active_players[num_courts * 4:]

        # 更新沒上場的人的等待時間
        for p in off_court_pool: p['wait_round'] += 1
        
        random.shuffle(on_court_pool)
        final_matches = []
        for i in range(num_courts):
            four_players = on_court_pool[i*4 : (i+1)*4]
            best_t1, best_t2 = self._get_best_match_combination(four_players)
            
            # 只要排定上場，就更新狀態
            for p in best_t1 + best_t2:
                p['play_count'] += 1
                p['wait_round'] = 0
            
            final_matches.append((best_t1, best_t2))
        
        self.save_data()
        return num_courts, final_matches

    def get_single_court_match(self, active_names, exclude_names):
        """
        單場補位邏輯：當單一場地結束時，從休息區抓人補位。
        exclude_names: 目前還在其他場地打球的人員名單。
        """
        # 1. 找出目前正在休息的人
        waiting_players = [p for p in self.players if p['name'] in active_names and p['name'] not in exclude_names]
        
        if len(waiting_players) < 4:
            return None # 休息人數不足 4 人，無法補位

        # 2. 挑選休息區中「最該上場」的 4 人
        waiting_players.sort(key=lambda x: (x['wait_round'] * 15 - x['play_count']), reverse=True)
        top_4 = waiting_players[:4]
        
        # 3. 針對這 4 人進行實力最佳匹配
        best_t1, best_t2 = self._get_best_match_combination(top_4)
        
        # 4. 更新狀態
        for p in best_t1 + best_t2:
            p['play_count'] += 1
            p['wait_round'] = 0
            
        # 5. 更新其他繼續休息的人的等待回合
        others_still_waiting = [p for p in waiting_players if p not in top_4]
        for p in others_still_waiting:
            p['wait_round'] += 1
            
        self.save_data()
        return (best_t1, best_t2)

    def report_result(self, winners, losers):
        """
        紀錄勝負結果，自動調整動態等級。
        """
        for p_name in winners:
            for p in self.players:
                if p['name'] == p_name:
                    p['level'] = round(min(14, p['level'] + 0.1), 2)
        
        for p_name in losers:
            for p in self.players:
                if p['name'] == p_name:
                    p['level'] = round(max(10, p['level'] - 0.1), 2)
        
        self.save_data()

# --- 測試代碼區塊 ---
if __name__ == "__main__":
    # 這部分只會在直接執行此 .py 檔時運行
    app = BadmintonApp()
    # (此處可加入測試用的 add_player 邏輯)