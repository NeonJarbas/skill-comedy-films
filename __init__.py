from os.path import join, dirname

from ovos_plugin_common_play.ocp import MediaType, PlaybackType
from ovos_utils.parse import fuzzy_match
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill, \
    ocp_search, ocp_featured_media
from youtube_archivist import IAArchivist


class ComedyFilmsSkill(OVOSCommonPlaybackSkill):

    def __init__(self):
        super().__init__("ComedyFilms")
        self.supported_media = [MediaType.BLACK_WHITE_MOVIE, MediaType.MOVIE, MediaType.GENERIC]
        self.skill_icon = join(dirname(__file__), "ui", "comedyfilms_icon.gif")
        self.archive = IAArchivist("Comedy_Films")

    def initialize(self):
        self.archive.bootstrap_from_url(
            f"https://github.com/OpenJarbas/streamindex/raw/main/{self.archive.db.name}.json")

    def normalize_title(self, title):
        title = title.lower().strip()
        title = self.remove_voc(title, "movie")
        title = self.remove_voc(title, "play")
        title = self.remove_voc(title, "video")
        title = title.replace("|", "").replace('"', "") \
            .replace(':', "").replace('”', "").replace('“', "") \
            .strip()
        return " ".join(
            [w for w in title.split(" ") if w])  # remove extra spaces

    def match_skill(self, phrase, media_type):
        score = 0
        if self.voc_match(phrase, "movie") or media_type == MediaType.MOVIE:
            score += 10
        if self.voc_match(phrase, "old"):
            score += 30
        if self.voc_match(phrase, "public_domain"):
            score += 15
        if self.voc_match(phrase, "comedy"):
            score += 25
        return score

    def calc_score(self, phrase, match, base_score=0):
        score = base_score
        score += 100 * fuzzy_match(phrase.lower(), match["title"].lower())
        return min(100, score)

    def get_playlist(self, score=50):
        return {
            "match_confidence": score,
            "media_type": MediaType.BLACK_WHITE_MOVIE,
            "playlist": self.featured_media(),
            "playback": PlaybackType.VIDEO,
            "skill_icon": self.skill_icon,
            "image": self.skill_icon,
            "skill_id": self.skill_id,
            "title": "Silent Hall of Fame (Movie Playlist)",
            "author": "Internet Archive"
        }

    @ocp_search()
    def search_db(self, phrase, media_type):
        base_score = self.match_skill(phrase, media_type)
        if media_type == MediaType.BLACK_WHITE_MOVIE:
            # only search db if user explicitly requested movies
            phrase = self.normalize_title(phrase)
            for _, video in self.archive.db.items():
                yield {
                    "title": video["title"],
                    "image": self.skill_icon,
                    "match_confidence": self.calc_score(phrase, video, base_score),
                    "media_type": MediaType.BLACK_WHITE_MOVIE,
                    "uri": video["streams"][0],  # TODO format selection
                    "playback": PlaybackType.VIDEO,
                    "skill_icon": self.skill_icon,
                    "skill_id": self.skill_id
                }

    @ocp_featured_media()
    def featured_media(self):
        return [{
            "title": video["title"],
            "image": self.skill_icon,
            "match_confidence": 70,
            "media_type": MediaType.BLACK_WHITE_MOVIE,
            "uri": video["streams"][0],  # TODO format selection
            "playback": PlaybackType.VIDEO,
            "skill_icon": self.skill_icon,
            "skill_id": self.skill_id
        } for _, video in self.archive.db.items() if video.get("streams")]


def create_skill():
    return ComedyFilmsSkill()
