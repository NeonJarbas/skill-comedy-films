from os.path import join, dirname

from json_database import JsonStorage

from ovos_utils.ocp import MediaType, PlaybackType
from ovos_workshop.decorators.ocp import ocp_search, ocp_featured_media
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill


class ComedyFilmsSkill(OVOSCommonPlaybackSkill):
    def __init__(self, *args, **kwargs):
        self.supported_media = [MediaType.SILENT_MOVIE, MediaType.BLACK_WHITE_MOVIE]
        self.skill_icon = join(dirname(__file__), "ui", "comedyfilms_icon.gif")
        self.archive = {v["streams"][0]: v for v in JsonStorage(f"{dirname(__file__)}/Comedy_Films.json").values()
                        if v["streams"]}
        super().__init__(*args, **kwargs)
        self.load_ocp_keywords()

    def load_ocp_keywords(self):
        bw_movies = []
        silent_movies = []

        for url, data in self.archive.items():
            t = data["title"].split("|")[0].split("(")[0].strip()
            if data.get("sound") in ["silent", "Silent, No Music"] or \
                    any(a in data["collection"] for a in ["silent_films"]) or \
                    any(a in data["tags"] for a in ["Silent", " silent", "silent"]):
                silent_movies.append(t)
                if ":" in t:
                    t1, t2 = t.split(":", 1)
                    silent_movies.append(t1.strip())
                    silent_movies.append(t2.strip())
            else:
                bw_movies.append(t)
                if ":" in t:
                    t1, t2 = t.split(":", 1)
                    bw_movies.append(t1.strip())
                    bw_movies.append(t2.strip())

        self.register_ocp_keyword(MediaType.BLACK_WHITE_MOVIE,
                                  "bw_movie_name", bw_movies)
        self.register_ocp_keyword(MediaType.SILENT_MOVIE,
                                  "silent_movie_name", silent_movies)
        self.register_ocp_keyword(MediaType.MOVIE,
                                  "movie_streaming_provider",
                                  ["ComedyFilms",
                                   "Comedy Films",
                                   "Classic Comedy Films",
                                   "Vintage Comedy Films"])

    def get_playlist(self, score=50, num_entries=25):
        pl = self.featured_media()[:num_entries]
        return {
            "match_confidence": score,
            "media_type": MediaType.MOVIE,
            "playlist": pl,
            "playback": PlaybackType.VIDEO,
            "skill_icon": self.skill_icon,
            "image": self.skill_icon,
            "title": "Vintage Comedy Films (Movie Playlist)",
            "author": "Vintage Comedy Films"
        }

    @ocp_search()
    def search_db(self, phrase, media_type):
        base_score = 15 if media_type in [MediaType.MOVIE, MediaType.BLACK_WHITE_MOVIE] else 0
        entities = self.ocp_voc_match(phrase)

        bw_title = entities.get("bw_movie_name")
        s_title = entities.get("silent_movie_name")
        skill = "movie_streaming_provider" in entities  # skill matched

        base_score += 30 * len(entities)

        if bw_title or s_title:
            candidates = self.archive.values()
            media_type = MediaType.MOVIE

            if bw_title:
                media_type = MediaType.BLACK_WHITE_MOVIE
                base_score += 20
                candidates = [video for video in self.archive.values()
                              if bw_title.lower() in video["title"].lower()]
            elif s_title:
                media_type = MediaType.SILENT_MOVIE
                base_score += 25
                candidates = [video for video in self.archive.values()
                              if s_title.lower() in video["title"].lower()]

            for video in candidates:
                yield {
                    "title": video["title"],
                    "match_confidence": min(100, base_score),
                    "media_type": media_type,
                    "uri": video["streams"][0],
                    "playback": PlaybackType.VIDEO,
                    "skill_icon": self.skill_icon,
                    "skill_id": self.skill_id,
                    "image": video["images"][0] if video["images"] else self.skill_icon
                }

        if skill:
            yield self.get_playlist()

    @ocp_featured_media()
    def featured_media(self):
        return [{
            "title": video["title"],
            "match_confidence": 70,
            "media_type": MediaType.MOVIE,
            "uri": video["streams"][0],
            "playback": PlaybackType.VIDEO,
            "skill_icon": self.skill_icon,
            "skill_id": self.skill_id
        } for video in self.archive.values()]


if __name__ == "__main__":
    from ovos_utils.messagebus import FakeBus

    s = ComedyFilmsSkill(bus=FakeBus(), skill_id="t.fake")
    for r in s.search_db("play Fatal Glass of Beer", MediaType.BLACK_WHITE_MOVIE):
        print(r)
        # {'title': 'The Fatal Glass of Beer', 'match_confidence': 65, 'media_type': <MediaType.BLACK_WHITE_MOVIE: 20>, 'uri': 'https://archive.org/download/Fatal_Glass_of_Beer_1933/Fatal_Glass_of_Beer.mp4', 'playback': <PlaybackType.VIDEO: 1>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png'}
        # {'title': 'Fatal Glass of Beer', 'match_confidence': 65, 'media_type': <MediaType.BLACK_WHITE_MOVIE: 20>, 'uri': 'https://archive.org/download/fatal_glass_of_beer/fatal_glass_of_beer.mp4', 'playback': <PlaybackType.VIDEO: 1>, 'skill_icon': 'https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/master/ovos_plugin_common_play/ocp/res/ui/images/ocp.png', 'skill_id': 't.fake', 'image': 'https://archive.org/download/fatal_glass_of_beer/fatal_glass_of_beer.png'}
