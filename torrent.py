import requests
import re
import os
from art import *
from tqdm import tqdm
from bs4 import BeautifulSoup


class Show:
    def __init__(self, user_show):
        self.base_url = "https://eztv.re/search/"
        if not user_show:
            user_show = "game of thrones"
        self.full_url = self.base_url + user_show
        self.html_doc = self._fetch_html()
        self.soup = BeautifulSoup(self.html_doc, "html.parser")

        self.episodes = []
        self.rated_episodes = []
        self.sorted_episodes = []
        self.selected_episodes = []

        self._parse_episodes()
        self._rate_episodes()
        self._sort_episodes()
        self._select_episodes()
        self._print_info()

    def _print_info(self):
        print(
            f"Found {len(self.selected_episodes)} episodes from {int(self.selected_episodes[-1]['season'])} seasons."
        )

    def _select_episodes(self):
        buffer = []
        prev_sortkey = None
        for episode in self.sorted_episodes:
            if episode["sortkey"] != prev_sortkey:
                self._process_buffer(buffer)
                buffer = []
                buffer.append(episode)
                prev_sortkey = episode["sortkey"]
                continue

            buffer.append(episode)
            prev_sortkey = episode["sortkey"]

    def _process_buffer(self, buffer):
        if not buffer:
            return
        max_rating_episode = max(buffer, key=lambda x: x["rating"])
        self.selected_episodes.append(max_rating_episode)

    def _parse_episodes(self):
        for episode in tqdm(self.soup.find_all("tr", class_="forum_header_border")):
            try:
                self._make_episodes(episode)
            except Exception as e:
                pass

    def _rate_episodes(self):
        for episode in self.episodes:
            # Disqualify
            if 1600 < episode["size"] < 200:
                continue
            if episode["quality"] and episode["quality"] < 360:
                continue
            if episode["seeds"] and episode["seeds"] < 1:
                continue
            if not episode["magnet"]:
                continue

            # Low rating
            episode["rating"] = 0
            # High rating
            if 1200 > episode["size"] > 400:
                episode["rating"] = 1
                # Really high rating
                if episode["quality"]:
                    if episode["quality"] > 720:
                        episode["rating"] = 2

            self.rated_episodes.append(episode)

    def _sort_episodes(self):
        self.sorted_episodes = sorted(self.rated_episodes, key=lambda x: x["sortkey"])

    def _make_episodes(self, episode):
        title = str(episode.find("a", class_="epinfo").get_text())
        season, ep_number = self._get_season_and_episode(title)
        sortkey = season + ep_number
        quality = self._get_quality(title)
        cells = episode.find_all("td")
        size = self._get_size(cells)
        age = str(cells[4].contents[0])
        seeds = self._get_seeds(cells)
        magnet = str(episode.find("a", class_="magnet")["href"])

        episode_dict = {
            "title": title,
            "season": season,
            "episode": ep_number,
            "sortkey": sortkey,
            "quality": quality,
            "size": size,
            "age": age,
            "seeds": seeds,
            "magnet": magnet,
        }
        self.episodes.append(episode_dict)

    def _get_quality(self, title):
        quality = re.search(r" (\d{3,4})p ", title)
        if quality:
            quality = int(quality[1])

        return quality

    def _get_season_and_episode(self, title):
        title_match = re.search(r"[Ss](\d\d)[Ee](\d\d)", title)
        if not title_match:
            title_match = re.search(" (\d+)x(\d+) ", title)
        if not title_match:
            raise Exception("Could not get Season / Episode.")
        if title_match:
            season = "0" + title_match[1] if len(title_match[1]) < 2 else title_match[1]
            ep_number = (
                "0" + title_match[2] if len(title_match[2]) < 2 else title_match[2]
            )
        return season, ep_number

    def _get_seeds(self, cells):
        seeds = str(cells[5].contents[0].get_text())
        if seeds.isnumeric():
            seeds = int(seeds)
        else:
            raise Exception("No Seeds.")
        return seeds

    def _get_size(self, cells):
        if not cells[3].contents:
            raise Exception("Could not get Size.")
        else:
            size_text = str(cells[3].contents[0])
            size = float(re.search(r"^(\d+\.\d+)", size_text)[1])
            if "GB" in size_text:
                size = size * 1000
            size = int(size)
        return size

    def _fetch_html(self):
        print("Fetching search results...")
        html_doc = requests.get(self.full_url).text
        print("Done fetching...")
        return html_doc

    def download_episodes(self, user_range):
        if user_range == "all":
            min, max = 0, len(self.selected_episodes)
        if "-" in user_range:
            min, max = user_range.split("-")
            min = int(min)
            max = int(max)
        if 0 < int(user_range) < 100:
            min = int(user_range)
            max = int(user_range)
        else:
            print("Wrong input")
            return
        for episode in self.selected_episodes:
            if int(episode["season"]) in range(min, max):
                self._download_magnet(episode["magnet"])

    def _download_magnet(self, magnet):
        if os.name == "nt":
            os.startfile(magnet)
        else:
            os.system("xdg-open " + magnet)


def main():
    tprint(
        """Welcome
        to
        Lazy Torrent""",
        font="chunky",
    )
    user_show = input("Let's get started! \nWhat show do you want to watch?\n")
    torrent = Show(user_show)
    user_range = input(
        """What season do you want to download? \n
    Type the season number (1, 2, 3 etc.) to download single seasons. \n
    Type a range (3-5) to download several seasons. \n
    Type "all" to download the entire catalogue.\n"""
    )

    torrent.download_episodes(user_range)


if __name__ == "__main__":
    main()
