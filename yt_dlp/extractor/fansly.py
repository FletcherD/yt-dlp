from .common import InfoExtractor
from ..utils import ExtractorError
import json
import urllib
from ..utils import (
    NO_DEFAULT,
    ExtractorError,
    clean_html,
    determine_ext,
    format_field,
    int_or_none,
    merge_dicts,
    orderedSet,
    remove_quotes,
    remove_start,
    str_to_int,
    update_url_query,
    url_or_none,
    urlencode_postdata,
)

class FanslyIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?fansly\.com/post/(?P<id>[0-9]+)'

    _API_URL = r'https://apiv3.fansly.com/api/v1'

    _TESTS = [{
        'url': 'https://fansly.com/post/614181860624310272',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            # For videos, only the 'id' and 'ext' fields are required to RUN the test:
            'id': '614181860624310272',
            'ext': 'mp4',
            # Then if the test run fails, it will output the missing/incorrect fields.
            # Properties can be added as:
            # * A value, e.g.
            #     'title': 'Video title goes here',
            # * MD5 checksum; start the string with 'md5:', e.g.
            #     'description': 'md5:098f6bcd4621d373cade4e832627b4f6',
            # * A regular expression; start the string with 're:', e.g.
            #     'thumbnail': r're:^https?://.*\.jpg$',
            # * A count of elements in a list; start the string with 'count:', e.g.
            #     'tags': 'count:10',
            # * Any Python type, e.g.
            #     'view_count': int,
        }
    }]

    def call_api(self, endpoint_name, video_id, params):
        params['ngsw-bypass'] = 'true'
        api_response = self._download_json(f'{self._API_URL}/{endpoint_name}', video_id,
                                   query=params,
                                   headers={
                                       'authorization': f'NjE0NjE1MzAxNDA0NzY2MjA4OjE6MjoxYTA2MmUzYzVkZmFiYjE2N2ZhNWFmNDViMDYzMWU',
                                       'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                                       'cookie': """f-v-d=1703801452806; f-d=447830839682674688; fansly-d=447830839682674688; __zlcmid=1GnlxfWjoytmiqe; _gcl_au=1.1.1938705187.1707853708; _ga=GA1.1.941351224.1707853708; f-v-v=0.33.15; _ga_BZSVNWD5W8=GS1.1.1708026775.10.1.1708028013.59.0.0; fansly-ts-info={"tso":-1449,"sts":1708028012499,"cts":1708028013948}; amp_4fb08e=dscb4wZx27uBIPVjQVKEak...1hmn58hgb.1hmn6ebdc.1a.0.1a"""})
        return api_response['response']

    def get_media(self, media_item):
        variants = media_item['variants']
        for variant in variants:
            locations = variant['locations']
            for location in locations:
                print(location['location'])

    def get_variant_as_formats(self, variant_item):
        location = variant_item['locations'][0]
        format_url = location['location']
        formats = []

        if 'metadata' in location:
            metadata = location['metadata']
            url_parsed = urllib.parse.urlparse(format_url)
            url_path = url_parsed.path.rsplit('/', maxsplit=1)[0]
            self._set_cookie(url_parsed.hostname, 'CloudFront-Key-Pair-Id', metadata.get('Key-Pair-Id', ''), path=url_path)
            self._set_cookie(url_parsed.hostname, 'CloudFront-Policy', metadata.get('Policy', ''), path=url_path)
            self._set_cookie(url_parsed.hostname, 'CloudFront-Signature', metadata.get('Signature', ''), path=url_path)

        ext = determine_ext(format_url)
        print(ext)
        if ext == 'm3u8':
            formats.extend(self._extract_m3u8_formats(
                format_url, variant_item['id'], 'mp4', entry_protocol='m3u8_native',
                m3u8_id='hls', fatal=False))
            
        formats.append({
            'url': format_url,
            'format_id': str(variant_item['type']),
            'width': variant_item['width'],
            'height': variant_item['height'],
        })
        return formats

    def get_media_item_as_video(self, media_item):
        video = {
            '_type': 'video',
            'id': media_item['id'],
            'title': '',
            'formats': sum([self.get_variant_as_formats(variant) for variant in media_item['variants']], [])
        }
        return video

    def get_post_as_playlist(self, posts_info):
        post_item = posts_info['posts'][0]
        videos = [self.get_media_item_as_video(account_media_item['media']) for account_media_item in posts_info['accountMedia']]
        playlist = {
            '_type': 'playlist',
            'id': post_item['id'],
            'title': '',
            'description': post_item['content'],
            'entries': videos
        }
        return playlist

    def _real_extract(self, url):
        post_id = self._match_id(url)

        posts_info = self.call_api('post', post_id, {'ids': post_id})
        playlist = self.get_post_as_playlist(posts_info)

        return playlist
