import os
import re
import sys
from art import tprint


class DL:
    def prompt_download(self, episodes_list):
        user_range = input(
            "What season/episode do you want to download? \n"
            "Type S01E01 for the first episode of the first season. \n"
            "Type S01E01-S03E12 to download a range of episodes.\n"
            "Type S01 to dowload season 1.\n"
            "Type S01-S3 to download a range of seasons.\n"
            "Type 'all' to download the entire catalogue.\n"
            "Type 'x' to cancel\n"
        )
        self.download_episodes(episodes_list, user_range)

    def download_episodes(self, episodes_list, user_range):
        min, max = self.get_sortkey_range(user_range)
        # ep_range = range(min, max)
        for episode in episodes_list:
            if int(min) <= int(episode["sortkey"]) <= int(max):
                self.download_magnet(episode["magnet"])

    def get_sortkey_range(self, user_range):
        # x
        if user_range.lower() == "x":
            sys.exit()
        # all
        if user_range.lower() == "all":
            min, max = "0000", "9999"
            return min, max

        # S01E01-S02E01
        s_e_range_match = re.match(
            r"^[Ss](\d\d)[Ee](\d\d)-[Ss](\d\d)[Ee](\d\d)$", user_range
        )
        if s_e_range_match:
            min = s_e_range_match[1] + s_e_range_match[2]
            max = s_e_range_match[3] + s_e_range_match[4]
            return min, max
        # S01-S02
        s_range_match = re.match(r"^[Ss](\d\d)-[Ss](\d\d)$", user_range)
        if s_range_match:
            min = s_range_match[1] + "00"
            max = s_range_match[2] + "99"
            return min, max
        # S01E03
        s_e_match = re.match(r"^[Ss](\d\d)[Ee](\d\d)$", user_range)
        if s_e_match:
            min = s_e_match[1] + s_e_match[2]
            return min, min
        # S01
        s_match = re.match(r"^[Ss](\d\d)$", user_range)
        if s_match:
            min = s_match[1] + "00"
            max = s_match[1] + "99"
            return min, max
        return None

    def download_magnet(self, magnet):
        if os.name == "nt":
            os.startfile(magnet)
        else:
            os.system("xdg-open " + magnet)

    def show_all_episodes(self, episodes_list):
        prev_season = None
        for episode in episodes_list:
            if episode["season"] != prev_season:
                print("-------------------------------")
            print(episode["title"])
            prev_season = episode["season"]
