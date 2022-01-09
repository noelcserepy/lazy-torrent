import requests
import re
import urllib.parse as parse
from tqdm import tqdm
from bs4 import BeautifulSoup


class Show:
    def __init__(self, user_show):
        self.base_url_eztv = "https://eztv.re/search/"
        self.base_url_pb = "https://thepiratebay.asia/s/?q="
        if not user_show:
            user_show = "game of thrones"
        self.full_url_eztv = self.base_url_eztv + user_show
        self.full_url_pb = self.base_url_pb + parse.quote_plus(user_show)
        self.html_eztv = self._fetch_html_eztv(self.full_url_eztv)
        self.html_pb = ""
        print("Fetching search results from PirateBay...")
        progress_bar = tqdm(total=100)
        self._fetch_html_pb(self.full_url_pb, progress_bar)
        self.soup_eztv = BeautifulSoup(self.html_eztv, "html.parser")
        self.soup_pb = BeautifulSoup(self.html_pb, "html.parser")

        self.episodes = []
        self.rated_episodes = []
        self.sorted_episodes = []
        self.selected_episodes = []

        self._parse_episodes_pb()
        self._parse_episodes_eztv()
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

    def _parse_episodes_eztv(self):
        for episode in tqdm(
            self.soup_eztv.find_all("tr", class_="forum_header_border")
        ):
            try:
                self._make_episodes_eztv(episode)
            except Exception as e:
                print(e)

    def _parse_episodes_pb(self):
        for episode in tqdm(self.soup_pb.find_all("tr")):
            try:
                self._make_episodes_pb(episode)
            except Exception as e:
                print(e)

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

    def _make_episodes_eztv(self, episode):
        title = str(episode.find("a", class_="epinfo").get_text()).strip()
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

    def _make_episodes_pb(self, episode):
        data_type = str(
            episode.find("a", {"title": "More from this category"}).get_text()
        ).strip()
        if data_type != "Video":
            return

        title = str(episode.find("a", class_="detLink").get_text()).strip()
        season, ep_number = self._get_season_and_episode(title)
        sortkey = season + ep_number
        quality = self._get_quality(title)
        magnet = str(
            episode.find("a", {"title": "Download this torrent using magnet"})["href"]
        )
        size = self._get_size_pb(episode)
        age = 0
        seeds, leechers = self._get_seeds_and_leech_pb(episode)

        episode_dict = {
            "title": title,
            "season": season,
            "episode": ep_number,
            "sortkey": sortkey,
            "quality": quality,
            "size": size,
            "age": age,
            "seeds": seeds,
            "leechers": leechers,
            "magnet": magnet,
        }
        self.episodes.append(episode_dict)

    def _get_seeds_and_leech_pb(self, episode):
        tds = episode.find_all("td", {"align": "right"})
        seeds = int(str(tds[-2].get_text()).strip())
        leechers = int(str(tds[-1].get_text()).strip())
        return seeds, leechers

    def _get_size_pb(self, episode):
        size_text = str(episode.find("font", class_="detDesc").get_text())
        size_match = re.search(r"Size (\d+\.\d+).+([MiBG]{3})", size_text)
        if size_match:
            size = float(size_match[1])
            if size_match[2] == "GiB":
                size = size * 1000
        return int(size)

    def _get_quality(self, title):
        quality = re.search(r" (\d{3,4})p ", title)
        if quality:
            quality = int(quality[1])

        return quality

    def _get_season_and_episode(self, title):
        title_match = re.search(r"[Ss](\d\d)[Ee](\d\d)", title)
        if not title_match:
            title_match = re.search(r" (\d+)x(\d+) ", title)
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

    def _fetch_html_eztv(self, full_url):
        print("Fetching search results from eztv...")
        html_doc = requests.get(full_url).text
        print("Done fetching...")
        return html_doc

    def _fetch_html_pb(self, full_url, progress_bar):
        progress_bar.update(1)
        html_doc = requests.get(full_url).text
        self.html_pb += html_doc
        soup_pb = BeautifulSoup(html_doc, "html.parser")
        next_image = soup_pb.find("img", {"alt": "Next"})
        if not next_image:
            return
        next_search = next_image.find_parent("a")["href"].split("/search/")[1]
        next_page = self.base_url_pb + next_search
        if next_page:
            self._fetch_html_pb(next_page, progress_bar)
