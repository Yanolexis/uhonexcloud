import youtube_dl
import os

class YouTube(object):
    def get_youtube_info(self, url):
        yt_opt = {
            'no_warnings':True,
            'ignoreerrors':True,
            'restrict_filenames':True,
            'dumpsinglejson':True,
            'format':'best[protocol=https]/best[protocol=http]/bestvideo[protocol=https]/bestvideo[protocol=http]'
                  }
        ydl = youtube_dl.YoutubeDL(yt_opt)
        with ydl:
            result = ydl.extract_info(
                url,
                download=False # We just want to extract the info
            )
        return result

    def filter_formats(self, formats):
        filter = []
        for f in formats:
            if '(DASH video)' in f['format']: continue
            if f['ext'] == 'mp4':
                if f['acodec'] =='mp4a.40.2':
                     filter.append(f)
        return filter
