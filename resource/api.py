import json, pprint
import requests

class Holodex:
    def __init__(self, token, channel_id):
        self._token = token
        self._channel_id = channel_id

    def _get_live_url(self):
        base = 'https://holodex.net/api/v2/live'
        params = []
        params.append(f'channel_id={self._channel_id}')
        params.append(f'status=live,upcoming')
        params.append(f'limit=5')
        params.append(f'order=asc')
        params.append(f'sort=start_scheduled')
        params.append(f'include=live_info')
        return base + '?' + '&'.join(params)

    # Blokcing api call
    def get_live(self):
        response = requests.get(self._get_live_url(), headers={'X-APIKEY': self._token})
        if response.status_code != 200:
            return None, response.status_code
        return response.json(), response.status_code

class YoutubeData:
    def __init__(self, token):
        self._token = token
        self._channel_id = ''
        self._video_id = ''
        self._etag_video = ''

    def set_channel_id(self, channel_id):
        self._channel_id = channel_id

    def set_video_id(self, video_id):
        self._video_id = video_id

    def get_video_list(self):
        base = 'https://www.googleapis.com/youtube/v3/videos'
        params = []
        params.append(f'part=liveStreamingDetails')
        params.append(f'id={self._video_id}')
        params.append(f'key={self._token}')

        headers = {'If-None-Match': self._etag_video}

        response = requests.get(base + '?' + '&'.join(params), headers=headers)
        if response.status_code == 304:
            return None, response.status_code
        if response.status_code != 200:
            return None, response.status_code
        result = response.json()
        self._etag_video = result['etag']
        return result, response.status_code

with open('../src/config.json') as f :
    s = f.read()
    config = json.loads(s)

api_holodex = Holodex(config['key_holodex'], 'UCdn5BQ06XqgXoAxIhbqw5Rg')
api_youtube = YoutubeData(config['key_youtube'])
resp, code = api_holodex.get_live()
print(f'Holodex API Call [Code: {code}]')
pprint.pprint(resp)

api_youtube.set_video_id(resp[0]['id'])
resp, code = api_youtube.get_video_list()
print(f'Youtube API Call [Code: {code}]')
pprint.pprint(resp)


