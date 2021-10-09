import urllib.request
import urllib.parse
import json
import shutil
import logging
import os


def create_forvo_fname(word):
    return "pronunciation_ru_{}.mp3".format(word)


class ForvoEntry(object):
    def __init__(self, raw):
        self.username = raw["username"]
        self.word = raw["word"]
        self.sex = "male" if raw["sex"] == "m" else "female"
        self.country = raw["country"]
        self.rating = raw["rate"]
        self.num_votes = raw["num_votes"]
        self.path = raw["pathmp3"]

    def download(self, out_dir=''):
        hdr = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}
        req = urllib.request.Request(self.path, headers=hdr)
        of = os.path.join(out_dir, create_forvo_fname(self.word))
        with urllib.request.urlopen(req) as response, open(of, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)

        return of

    def __str__(self):
        return "Pronunciation by {} ({} from {})\n\tRating {} ({} votes)".format(self.username, self.sex, self.country, self.rating, self.num_votes)


class ForvoResults(object):
    def __init__(self, dat, preferred_users=None):
        self.logger = logging.getLogger(__name__)
        self._index = 0

        self._num_pron = dat.get('attributes', {}).get('total', 0)
        self.logger.debug('Number of pronunciations found: %d', self.num_pron)

        preferred_users = [] if preferred_users is None else preferred_users

        self._prons = []
        self._preferred_prons = []
        for en in dat.get('items', []):
            fe = ForvoEntry(en)
            self._prons.append(fe)

            if fe.username in preferred_users:
                self._preferred_prons.append(fe)

        if self._prons:
            self._prons.sort(key=lambda x: x.rating, reverse=True)

    @property
    def num_pron(self):
        return self._num_pron

    @num_pron.setter
    def num_pron(self, val):
        self._num_pron = val

    def get_preferred(self):
        if self._preferred_prons:
            return self._preferred_prons[0]

    def download_preferred(self):
        if self.get_preferred():
            self.get_preferred().download()
            return True
        else:
            return False

    def get(self, idx):
        return self._prons[idx]

    def __iter__(self):
        return self

    def __next__(self):
        if self._index < self.num_pron:
            result = self._prons[self._index]
            self._index += 1
            return result
        raise StopIteration

    def __str__(self):
        self_str = '{} of pronunciations found:\n'.format(self.num_pron)
        for en in self._prons:
            self_str += str(en) + '\n\n'

        return self_str

    def get_highest_rating(self):
        return self._prons[0]


class ForvoAgent(object):
    def __init__(self, api_key):
        self.logger = logging.getLogger(__name__)

        if api_key is None:
            raise Exception('Must provide an api key to use forvo parser')
        self.api_key = api_key

        self.base_url = "https://apifree.forvo.com/action/word-pronunciations/format/json/word/"
        self._data = {}

    def query(self, word, language, preferred_users=None) -> ForvoResults:
        url = self.base_url + "{}/id_lang_speak/138/language/{}/key/{}/".format(urllib.parse.quote(word), language, self.api_key)
        hdr = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}
        req = urllib.request.Request(url, headers=hdr)

        try:
            response = urllib.request.urlopen(req)
        except Exception as e:
            self.logger.error("Error downloading file", exc_info=True)
            return ForvoResults({'attributes': {'total': 0}})

        return ForvoResults(json.loads(response.read()), preferred_users)


class ForvoParser:
    forvo = ForvoAgent(os.getenv('FORVO_API_KEY'))

    def __init__(self, pref_users=None, language='ru'):
        self.logger = logging.getLogger('ForvoParser')

        self.pref_users = [] if pref_users is None else pref_users
        self.language = language

    def download(self, word, out_dir):
        prons = ForvoParser.forvo.query(word, self.language, self.pref_users)

        if not prons.num_pron:
            self.logger.debug('No results found for word %s', word)
            return None

        if prons.get_preferred() is not None:
            selection = prons.get_preferred()
        else:
            selection = prons.get_highest_rating()

        if not os.path.exists(out_dir):
            os.mkdir(out_dir)

        return selection.download(out_dir)


if __name__ == '__main__':
    f = ForvoParser()
    res = f.download('идти', '.')
