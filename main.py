import pickle
import os
from art import tprint
from src.show import Show
from src.dl import DL


def main():
    tprint(
        """Welcome
        to
        Lazy Torrent""",
        font="chunky",
    )
    user_show = input(
        "Let's get started! Make sure your torrent client is open before you proceed.\n"
        "What show do you want to watch? \n"
    )

    if os.path.exists("./data.p"):
        data = pickle.load(open("./data.p", "rb"))
        if user_show in data.keys():
            stored_show = input(
                "Found existing search results for this show. Would you like to update the results? y/n \n"
            )
            if stored_show == "y":
                show = Show(user_show)
                data[user_show] = show.selected_episodes
                pickle.dump(data, open("./data.p", "wb"))
            DL.show_all_episodes(data[user_show])
            DL.prompt_download(data[user_show])
            return
        else:
            show = Show(user_show)
            data[user_show] = show.selected_episodes
            pickle.dump(data, open("./data.p", "wb"))
            DL.show_all_episodes(1, show.selected_episodes)
            DL.prompt_download(show.selected_episodes)
    else:
        show = Show(user_show)
        pickle.dump({user_show: show.selected_episodes}, open("./data.p", "wb"))
        DL.show_all_episodes(show.selected_episodes)
        DL.prompt_download(show.selected_episodes)


if __name__ == "__main__":
    main()
