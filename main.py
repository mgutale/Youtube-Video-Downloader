#! /usr/bin/env python3

from pytube import YouTube
from youtube_search import YoutubeSearch

def download():
    # input texts
    save_path = input('Enter the path you want to save the videos to: ')
    search_term = input('Enter the Search term on Youtube: ')
    number_of_videos = int(input('Enter the Number of videos to download: '))
    results = YoutubeSearch(search_term, max_results=number_of_videos).to_dict()
    url_yt = 'www.youtube.com'
    returned_urls = [_['url_suffix'] for _ in results]
    urls = [url_yt + str(i) for i in returned_urls]
    
    for url_link in urls:
        try:
            yt = YouTube(url_link)
        except:
            print("Connection Error")
    # resolution passed in the get() function
    ys = yt.streams.get_highest_resolution()

    try:
        # downloading the video
        ys.download(save_path)
    except:
        print("Some Error!")

    print('Video is now downloaded, Enjoy!')


if __name__ == '__main__':
    download()