import streamlit as st
from pytube import YouTube
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
import tempfile
import numpy as np
import whisper
import requests
import os

st.set_page_config(page_title="YouTube → TikTok Clips", layout="wide")
st.title("YouTube → TikTok Viral Clip Generator (Streamlit Cloud)")

# ---------------- Input ----------------
url = st.text_input("Enter YouTube Video URL:")

use_trending_audio = st.checkbox("Use trending TikTok audio?")

# Example trending sound URL (replace with live TikTok API if available)
trending_sound_url = "https://www.example.com/trending_tiktok_audio.mp3"

if url:
    st.info("Downloading YouTube video...")
    try:
        yt = YouTube(url)
        video_stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        tmp_video_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        video_stream.download(filename=tmp_video_file.name)
        st.success("Video downloaded!")
    except Exception as e:
        st.error(f"Failed to download video: {e}")
        st.stop()
    
    clip = VideoFileClip(tmp_video_file.name)
    duration = clip.duration
    st.write(f"Video Duration: {duration:.2f} seconds")
    
    # ---------------- Audio Extraction ----------------
    st.info("Extracting audio...")
    audio = clip.audio
    tmp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    audio.write_audiofile(tmp_audio_file.name, logger=None)
    
    # ---------------- Highlight Detection ----------------
    st.info("Detecting highlight moments...")
    audio_clip = AudioFileClip(tmp_audio_file.name)
    fps = 44100
    samples = audio_clip.to_soundarray(fps=fps)
    amplitudes = np.mean(np.abs(samples), axis=1)
    
    chunk_size = fps
    avg_amplitudes = [np.mean(amplitudes[i:i+chunk_size]) for i in range(0, len(amplitudes), chunk_size)]
    threshold = np.percentile(avg_amplitudes, 90)
    highlight_times = [i for i, a in enumerate(avg_amplitudes) if a >= threshold]
    
    highlights = []
    if highlight_times:
        start = highlight_times[0]
        for i in range(1, len(highlight_times)):
            if highlight_times[i] > highlight_times[i-1] + 1:
                end = highlight_times[i-1]
                highlights.append((start, end))
                start = highlight_times[i]
        highlights.append((start, highlight_times[-1]))
    
    # ---------------- Load Whisper ----------------
    st.info("Loading Whisper model for subtitles...")
    model = whisper.load_model("small")
    
    clips_with_scores = []
    
    # Fetch trending TikTok audio if checked
    if use_trending_audio:
        st.info("Fetching trending TikTok audio...")
        tmp_audio_trend = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        try:
            r = requests.get(trending_sound_url)
            tmp_audio_trend.write(r.content)
            tmp_audio_trend.flush()
            tiktok_audio = AudioFileClip(tmp_audio_trend.name)
        except Exception as e:
            st.warning(f"Could not fetch trending audio: {e}")
            tiktok_audio = None
    else:
        tiktok_audio = None
    
    # ---------------- Generate Clips ----------------
    st.info("Generating TikTok clips...")
    for start, end in highlights:
        start_sec = max(0, start)
        end_sec = min(duration, end+1)
        clip_len = end_sec - start_sec
        if clip_len < 5:
            continue
        
        subclip = clip.subclip(start_sec, min(end_sec, start_sec + 30))
        
        # Resize to vertical 9:16
        subclip = subclip.resize(height=1920)
        subclip = subclip.crop(x_center=subclip.w/2, width=1080)
        
        # Save temporary clip
        tmp_clip_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        subclip.write_videofile(tmp_clip_file.name, logger=None)
        
        # Transcribe
        result = model.transcribe(tmp_clip_file.name)
        text = result["text"].strip()
        
        # Add subtitles
        txt_clip = TextClip(text, fontsize=40, color='white', bg_color='black', method='caption', size=subclip.size)
        txt_clip = txt_clip.set_position(('center', 'bottom')).set_duration(subclip.duration)
        final_clip = CompositeVideoClip([subclip, txt_clip])
        
        # Add TikTok audio if available
        if tiktok_audio:
            audio_clip = tiktok_audio.set_duration(final_clip.duration)
            final_clip = final_clip.set_audio(audio_clip)
        
        # Virality score: energy + speech content
        energy_score = np.mean(avg_amplitudes[start:end])
        speech_score = len(text.split())
        virality_score = energy_score * 0.6 + speech_score * 0.4
        clips_with_scores.append((final_clip, virality_score))
    
    # Sort clips by virality
    clips_with_scores.sort(key=lambda x: x[1], reverse=True)
    
    # ---------------- Output Clips ----------------
    st.success(f"Generated {len(clips_with_scores)} TikTok-ready clips!")
    for i, (c, score) in enumerate(clips_with_scores):
        clip_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        c.write_videofile(clip_file.name, logger=None)
        st.video(clip_file.name)
        st.download_button(
            label=f"Download Clip {i+1} (Score: {score:.2f})",
            data=open(clip_file.name, "rb"),
            file_name=f"tiktok_clip_{i+1}.mp4",
            mime="video/mp4"
        )
    
    st.success("All clips are fully TikTok-ready!")

