import streamlit as st
from pytube import YouTube
from moviepy.editor import VideoFileClip
import tempfile

st.title("YouTube → TikTok Clip Generator (Simplified)")

# Input YouTube URL
url = st.text_input("Enter YouTube video URL:")

if url:
    try:
        st.info("Downloading video...")
        yt = YouTube(url)
        video_stream = yt.streams.filter(progressive=True, file_extension='mp4') \
                                 .order_by('resolution').desc().first()
        
        # Save to temporary file
        tmp_video_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        video_stream.download(filename=tmp_video_file.name)
        st.success("Video downloaded!")

        # Load video
        clip = VideoFileClip(tmp_video_file.name)
        duration = clip.duration
        st.write(f"Video duration: {duration:.2f} seconds")

        # Take first 30 seconds (or full video if shorter)
        end_time = min(30, duration)
        subclip = clip.subclip(0, end_time)

        # Resize to 9:16 vertical
        subclip = subclip.resize(height=1920)
        subclip = subclip.crop(x_center=subclip.w / 2, width=1080)

        # Save temporary output file
        tmp_clip_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        subclip.write_videofile(tmp_clip_file.name, logger=None)

        # Show video
        st.video(tmp_clip_file.name)

        # Download button
        st.download_button(
            label="Download TikTok Clip",
            data=open(tmp_clip_file.name, "rb"),
            file_name="tiktok_clip.mp4",
            mime="video/mp4"
        )
        st.success("Clip ready!")

    except Exception as e:
        st.error(f"Error: {e}")
