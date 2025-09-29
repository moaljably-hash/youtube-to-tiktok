import streamlit as st
from pytube import YouTube
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip
import tempfile
import requests

st.set_page_config(page_title="YouTube → TikTok Clips", layout="wide")
st.title("YouTube → TikTok Viral Clip Generator (Safe for Streamlit Cloud)")

# ---------------- Input ----------------
url = st.text_input("Enter YouTube Video URL:")
use_trending_audio = st.checkbox("Use trending TikTok audio?")

# Example trending sound URL (replace with actual URL if desired)
trending_sound_url = "https://www.example.com/trending_tiktok_audio.mp3"

if url:
    st.info("Downloading YouTube video...")
    try:
        yt = YouTube(url)
        video_stream = yt.streams.filter(progressive=True, file_extension='mp4') \
                                 .order_by('resolution').desc().first()
        tmp_video_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        video_stream.download(filename=tmp_video_file.name)
        st.success("Video downloaded!")
    except Exception as e:
        st.error(f"Failed to download video: {e}")
        st.stop()

    clip = VideoFileClip(tmp_video_file.name)
    duration = clip.duration
    st.write(f"Video Duration: {duration:.2f} seconds")

    # ---------------- Fetch trending audio ----------------
    tiktok_audio = None
    if use_trending_audio:
        st.info("Fetching trending TikTok audio...")
        try:
            tmp_audio_trend = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            r = requests.get(trending_sound_url)
            tmp_audio_trend.write(r.content)
            tmp_audio_trend.flush()
            tiktok_audio = AudioFileClip(tmp_audio_trend.name)
        except Exception as e:
            st.warning(f"Could not fetch trending audio: {e}")
            tiktok_audio = None

    # ---------------- Generate TikTok clip ----------------
    st.info("Generating TikTok-ready clip...")

    # Take the first 30 seconds (or full video if shorter)
    end_time = min(30, duration)
    subclip = clip.subclip(0, end_time)

    # Resize to vertical 9:16
    subclip = subclip.resize(height=1920)
    subclip = subclip.crop(x_center=subclip.w/2, width=1080)

    # Add trending audio if available
    if tiktok_audio:
        tiktok_audio = tiktok_audio.set_duration(subclip.duration)
        subclip = subclip.set_audio(tiktok_audio)

    # Save temporary clip for download
    tmp_clip_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    subclip.write_videofile(tmp_clip_file.name, logger=None)

    # Show video in Streamlit
    st.video(tmp_clip_file.name)

    # Download button
    st.download_button(
        label="Download TikTok Clip",
        data=open(tmp_clip_file.name, "rb"),
        file_name="tiktok_clip.mp4",
        mime="video/mp4"
    )

    st.success("Clip is ready for TikTok!")

