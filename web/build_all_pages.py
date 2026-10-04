#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
# SPDX-License-Identifier: Apache-2.0

"""Master site generator for Musedy AI Robot Companion.
Generates:
1. index.html - Meta Astryx Landing Page with interactive Robot Simulator
2. wiring.html - Interactive Pinout & Wiring Diagram with circuit highlights
3. deploy.html - Interactive Step-by-Step Deployment & Firmware Flashing Guide
Copies artifacts to both root / and docs/ for 100% GitHub Pages compatibility.
"""

import base64
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"

# Load images
img_blue_path = ROOT / "docs/designs/xiaozhi_computer_blue.png"
img_astro_path = ROOT / "docs/designs/concept1_astropod.png"

b64_blue = base64.b64encode(img_blue_path.read_bytes()).decode("ascii") if img_blue_path.exists() else ""
b64_astro = base64.b64encode(img_astro_path.read_bytes()).decode("ascii") if img_astro_path.exists() else ""

SHARED_HEAD = '''
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          fontFamily: {
            sans: ['"Plus Jakarta Sans"', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
            mono: ['"JetBrains Mono"', 'monospace'],
          },
          colors: {
            astryx: {
              canvas: '#06080F',
              subtle: '#0D111D',
              surface: '#111726',
              elevated: '#172033',
              border: 'rgba(255, 255, 255, 0.08)',
              borderFocus: '#00F0FF',
              primary: '#00F0FF',
              secondary: '#2563EB',
              accent: '#00F0FF',
            }
          },
          boxShadow: {
            'glow-cyan': '0 0 35px -5px rgba(0, 240, 255, 0.35)',
            'glow-cobalt': '0 0 35px -5px rgba(37, 99, 235, 0.35)',
          }
        }
      }
    }
  </script>
  <style>
    :root {
      --astryx-cyan: #00F0FF;
      --astryx-cobalt: #2563EB;
      --astryx-bg: #06080F;
    }
    body {
      background-color: #06080F;
      color: #F8FAFC;
      font-family: 'Plus Jakarta Sans', sans-serif;
      overflow-x: hidden;
    }
    .astryx-mesh {
      background-image: 
        radial-gradient(circle at 50% 0%, rgba(0, 240, 255, 0.12) 0%, transparent 60%),
        radial-gradient(circle at 85% 30%, rgba(37, 99, 235, 0.12) 0%, transparent 50%),
        radial-gradient(circle at 15% 70%, rgba(56, 189, 248, 0.10) 0%, transparent 50%);
    }
    .astryx-grid {
      background-size: 40px 40px;
      background-image: 
        linear-gradient(to right, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
    }
    .glass-card {
      background: rgba(17, 23, 38, 0.72);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.08);
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .glass-card:hover {
      border-color: rgba(0, 240, 255, 0.3);
      box-shadow: 0 12px 36px -10px rgba(0, 240, 255, 0.15);
    }
    .crt-screen {
      background: #020612;
      border: 3px solid #1E293B;
      box-shadow: inset 0 0 30px rgba(0, 240, 255, 0.15), 0 0 15px rgba(0, 240, 255, 0.2);
      position: relative;
    }
    .crt-screen::before {
      content: " ";
      display: block;
      position: absolute;
      top: 0; left: 0; bottom: 0; right: 0;
      background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.03), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.03));
      z-index: 10;
      background-size: 100% 3px, 6px 100%;
      pointer-events: none;
    }
    .text-balance {
      text-wrap: balance;
    }
    @keyframes wave {
      0%, 100% { height: 8px; }
      50% { height: 32px; }
    }
    .animate-wave {
      animation: wave 1.2s ease-in-out infinite;
    }
    @keyframes float {
      0%, 100% { transform: translateY(0px); }
      50% { transform: translateY(-10px); }
    }
    .animate-float {
      animation: float 6s ease-in-out infinite;
    }
  </style>
'''

NAV_HEADER = '''
  <!-- TOP STATUS BANNER (Meta Astryx Telemetry) -->
  <div class="border-b border-white/5 bg-black/40 backdrop-blur-md px-3 sm:px-4 py-1.5 text-xs font-mono text-slate-400">
    <div class="max-w-7xl mx-auto flex items-center justify-between">
      <div class="flex items-center space-x-2 sm:space-x-3">
        <span class="inline-flex items-center gap-1.5 shrink-0">
          <span class="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span class="text-emerald-400 font-semibold tracking-wider text-[11px] sm:text-xs">SYSTEM ONLINE</span>
        </span>
        <span class="text-white/20 hidden sm:inline">|</span>
        <span class="hidden sm:inline text-slate-400">CORE: ESP32-S3 DUAL-CORE 240MHz</span>
        <span class="hidden md:inline text-white/20">|</span>
        <span class="hidden md:inline text-slate-400">DISPLAY: 1.8" LANDSCAPE 160x128 (ST7735 / ST7789)</span>
      </div>
      <div class="flex items-center space-x-2 sm:space-x-4 shrink-0">
        <span class="text-cyan-400 text-[11px] sm:text-xs font-semibold">FW: v1.2-MUSEDY</span>
        <span class="text-white/20 hidden sm:inline">|</span>
        <a href="https://github.com/tody-agent/musedy" target="_blank" rel="noopener noreferrer" class="hover:text-cyan-300 transition-colors hidden sm:inline">GITHUB: tody-agent/musedy</a>
      </div>
    </div>
  </div>

  <!-- NAVIGATION HEADER -->
  <header class="sticky top-0 z-50 border-b border-white/10 bg-astryx-canvas/80 backdrop-blur-xl">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <!-- Logo Brand -->
      <a href="index.html" class="flex items-center space-x-3 group shrink-0">
        <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center font-bold text-black text-lg shadow-glow-cyan">
          M
        </div>
        <div class="flex flex-col">
          <span class="font-extrabold text-base tracking-tight text-white group-hover:text-cyan-400 transition-colors">
            MUSEDY<span class="text-cyan-400 font-black">.S3</span>
          </span>
          <span class="text-[10px] font-mono tracking-widest text-slate-400 uppercase -mt-1">Retro AI Companion</span>
        </div>
      </a>

      <!-- Desktop Nav Links -->
      <nav class="hidden md:flex items-center space-x-1 lg:space-x-2 text-sm font-medium text-slate-300">
        <a href="index.html#showcase" class="px-3 py-1.5 rounded-lg hover:text-cyan-300 hover:bg-slate-800/60 transition-colors">01. Vỏ Máy Tính</a>
        <a href="index.html#simulator" class="px-3 py-1.5 rounded-lg hover:text-cyan-300 hover:bg-slate-800/60 transition-colors">02. Trải Nghiệm Giọng Nói</a>
        <a href="wiring.html" class="px-3 py-1.5 rounded-lg text-cyan-400 hover:text-cyan-300 hover:bg-slate-800/60 transition-colors">03. Sơ Đồ Kết Nối</a>
        <a href="deploy.html" class="px-3 py-1.5 rounded-lg text-sky-400 hover:text-sky-300 hover:bg-slate-800/60 transition-colors">04. Hướng Dẫn Triển Khai</a>
        <a href="index.html#specs" class="px-3 py-1.5 rounded-lg hover:text-cyan-300 hover:bg-slate-800/60 transition-colors">05. Thông Số STL</a>
      </nav>

      <!-- Action Buttons -->
      <div class="flex items-center space-x-2 sm:space-x-3">
        <a href="https://github.com/tody-agent/musedy" target="_blank" rel="noopener noreferrer" 
           class="hidden sm:inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg border border-white/15 bg-slate-800/40 text-xs font-semibold text-white hover:bg-slate-800 hover:border-cyan-400/50 hover:text-cyan-300 transition-all whitespace-nowrap">
          <svg class="w-4 h-4 text-cyan-400 shrink-0" fill="currentColor" viewBox="0 0 24 24"><path fill-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clip-rule="evenodd"></path></svg>
          GitHub Repo
        </a>
        <a href="index.html#simulator" 
           class="inline-flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-2 rounded-xl border border-cyan-500/40 bg-cyan-500/10 text-xs font-bold text-cyan-300 hover:bg-cyan-500/20 active:scale-95 transition-all whitespace-nowrap shadow-glow-cyan">
          <svg class="w-4 h-4 shrink-0 text-cyan-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"></path></svg>
          <span>Thử Ngay</span>
        </a>
      </div>
    </div>
  </header>
'''

SHARED_FOOTER = '''
  <!-- FOOTER -->
  <footer class="border-t border-white/10 py-12 bg-astryx-canvas text-xs text-slate-400">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
      <!-- Brand & Copyright -->
      <div class="flex items-center space-x-3">
        <div class="w-7 h-7 rounded-lg bg-gradient-to-tr from-cyan-400 to-blue-500 flex items-center justify-center font-bold text-black text-sm">
          M
        </div>
        <div>
          <div class="text-white font-bold">MUSEDY S3 ROBOTICS</div>
          <div class="text-[11px] text-slate-400">Thiết kế bởi cộng đồng Maker • Mã nguồn mở theo giấy phép Apache-2.0</div>
        </div>
      </div>

      <!-- Links -->
      <div class="flex flex-wrap items-center gap-6 font-mono text-[11px]">
        <a href="wiring.html" class="hover:text-cyan-400 transition-colors">Sơ Đồ Kết Nối</a>
        <a href="deploy.html" class="hover:text-cyan-400 transition-colors">Hướng Dẫn Triển Khai</a>
        <a href="https://github.com/tody-agent/musedy" target="_blank" rel="noopener noreferrer" class="hover:text-cyan-400 transition-colors">GitHub Repository</a>
        <span class="text-white/20">|</span>
        <span class="text-cyan-300">OpenDesign &amp; Meta Astryx System</span>
      </div>
    </div>
  </footer>
'''

def generate_index_html():
    return f'''<!DOCTYPE html>
<html lang="vi" class="scroll-smooth">
<head>
  {SHARED_HEAD}
  <title>Musedy S3 • Robot Trí Tuệ Nhân Tạo Mini (Meta Astryx Edition)</title>
  <meta name="description" content="Robot Trí Tuệ Nhân Tạo Mini Musedy phong cách Máy Tính Cổ Điển Thập Niên 80 chạy ESP32-S3, màn hình màu tròn CRT, Voice Wakeup và tiếng Việt mượt mà.">
</head>
<body class="astryx-mesh astryx-grid min-h-screen antialiased selection:bg-cyan-500 selection:text-black">
  {NAV_HEADER}

  <!-- HERO SECTION -->
  <section id="hero" data-od-id="hero-section" class="relative pt-10 pb-16 md:pt-20 md:pb-32 overflow-hidden">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-center">
        
        <!-- Left Column: Copy & Value Proposition -->
        <div class="lg:col-span-7 flex flex-col space-y-6 text-left">
          
          <!-- Badge -->
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-cyan-500/30 bg-cyan-950/40 text-cyan-300 text-xs font-mono tracking-wider w-fit">
            <span class="inline-block w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
            MUSEDY AI ROBOT • META ASTRYX DESIGN SYSTEM
          </div>

          <!-- Main Heading -->
          <h1 class="text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-[1.15] text-balance">
            Robot Trí Tuệ Nhân Tạo <br>
            <span class="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-sky-300 to-blue-500">
              Musedy Máy Tính Mini
            </span>
          </h1>

          <!-- Subheading -->
          <p class="text-sm sm:text-base lg:text-lg text-slate-300 font-normal leading-relaxed max-w-2xl text-balance">
            Sự hội ngộ giữa hình hài máy tính <strong>Macintosh CRT thập niên 80</strong> màu Xanh Dương và bộ não trí tuệ nhân tạo thế hệ mới <strong>ESP32-S3</strong>: Voice Wakeup kích hoạt tức thì, giao tiếp tiếng Việt tự nhiên, màn hình màu tròn vintage và loa vòm đánh gầm 3W.
          </p>

          <!-- Key Metrics Pills -->
          <div class="grid grid-cols-3 gap-2 sm:gap-3 pt-2 max-w-lg w-full">
            <div class="glass-card p-2.5 sm:p-3 rounded-xl border border-white/10 text-center">
              <div class="text-lg sm:text-2xl font-black text-cyan-400 font-mono">0ms</div>
              <div class="text-[10px] sm:text-[11px] text-slate-400 font-medium whitespace-nowrap">Chi Phí TTS</div>
            </div>
            <div class="glass-card p-2.5 sm:p-3 rounded-xl border border-white/10 text-center">
              <div class="text-lg sm:text-2xl font-black text-sky-400 font-mono">30 FPS</div>
              <div class="text-[10px] sm:text-[11px] text-slate-400 font-medium whitespace-nowrap">Màn Hình SPI</div>
            </div>
            <div class="glass-card p-2.5 sm:p-3 rounded-xl border border-white/10 text-center">
              <div class="text-lg sm:text-2xl font-black text-blue-400 font-mono">&lt;280ms</div>
              <div class="text-[10px] sm:text-[11px] text-slate-400 font-medium whitespace-nowrap">Phản Hồi VAD</div>
            </div>
          </div>

          <!-- Dual CTAs -->
          <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-4 pt-4 w-full sm:w-auto">
            <a href="https://makerworld.com/en/models/1967811-xiaozhi-ai-computer-xiaozhi#profileId-2115633" target="_blank" rel="noopener noreferrer"
               class="justify-center px-5 sm:px-6 py-3.5 rounded-xl bg-gradient-to-r from-cyan-400 to-blue-500 font-bold text-black text-xs sm:text-sm shadow-glow-cyan hover:shadow-cyan-500/50 hover:brightness-110 active:scale-95 transition-all inline-flex items-center gap-2">
              <svg class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"></path></svg>
              <span>Tải File In 3D (MakerWorld)</span>
            </a>
            <a href="#simulator" 
               class="justify-center px-5 sm:px-6 py-3.5 rounded-xl border border-white/20 bg-white/5 font-semibold text-white text-xs sm:text-sm hover:bg-white/10 hover:border-cyan-400/60 active:scale-95 transition-all inline-flex items-center gap-2">
              <svg class="w-5 h-5 text-cyan-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              <span>Trải Nghiệm Giọng Nói Musedy</span>
            </a>
          </div>

          <!-- Verified Hardware compatibility note -->
          <div class="flex items-center gap-3 pt-2 text-xs text-slate-400 font-mono">
            <span class="inline-block w-2 h-2 rounded-full bg-cyan-400"></span>
            <span>Màn hình 1.8" xoay ngang 160x128 ST7735 (Chuẩn Vỏ Retro) &amp; tùy chọn 1.28" Tròn (GC9A01)</span>
          </div>

        </div>

        <!-- Right Column: Photorealistic Hero Render Showcase -->
        <div class="lg:col-span-5 relative flex justify-center items-center">
          <div class="absolute -inset-4 bg-gradient-to-tr from-cyan-500/20 via-blue-500/10 to-blue-600/20 rounded-3xl blur-3xl -z-10 animate-pulse-slow"></div>

          <div class="relative glass-card rounded-3xl p-4 border border-white/15 shadow-2xl animate-float">
            <div class="flex items-center justify-between pb-3 mb-3 border-b border-white/10 text-xs font-mono text-slate-400">
              <span class="flex items-center gap-2">
                <span class="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
                <span class="text-white font-semibold">MUSEDY COMPUTER EDITION</span>
              </span>
              <span class="bg-cyan-500/10 text-cyan-300 px-2 py-0.5 rounded border border-cyan-500/20 text-[10px]">COLOR: BLUE/CREAM</span>
            </div>

            <div class="relative overflow-hidden rounded-2xl bg-gradient-to-b from-slate-900/90 to-black border border-white/10 group">
              <img id="hero-showcase-img" 
                   src="data:image/png;base64,{b64_blue}" 
                   alt="Musedy S3 Retro Computer Blue Edition" 
                   class="w-full h-auto object-cover rounded-2xl transition-transform duration-700 group-hover:scale-105">
              
              <div class="absolute bottom-6 right-6 glass-card px-3 py-1.5 rounded-lg border border-white/20 text-[11px] font-mono text-slate-300 flex items-center gap-2 shadow-lg backdrop-blur-md">
                <span class="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping"></span>
                <span>Floppy Slot (Khe đĩa mềm)</span>
              </div>

              <div class="absolute top-6 left-6 glass-card px-3 py-1.5 rounded-lg border border-white/20 text-[11px] font-mono text-slate-300 flex items-center gap-2 shadow-lg backdrop-blur-md">
                <span class="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
                <span>4 Phím cứng xúc giác đỉnh</span>
              </div>
            </div>

            <div class="mt-4 pt-3 border-t border-white/10 flex items-center justify-between text-xs text-slate-400 font-mono">
              <span>DESIGN: 董老爺 (Mr. Dong)</span>
              <span class="text-cyan-400">MAKERWORLD #1967811</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  </section>

  <!-- INTERACTIVE VIRTUAL MUSEDY SIMULATOR -->
  <section id="simulator" data-od-id="simulator-section" class="py-16 md:py-24 border-y border-white/10 bg-astryx-subtle/60 relative">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      
      <div class="text-center max-w-3xl mx-auto mb-12">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-blue-500/30 bg-blue-950/40 text-blue-300 text-xs font-mono tracking-wider mb-3">
          LIVE INTERACTIVE SIMULATOR
        </div>
        <h2 class="text-3xl sm:text-4xl font-extrabold text-white tracking-tight text-balance">
          Trải Nghiệm Màn Hình Cảm Xúc &amp; Giọng Nói Musedy S3
        </h2>
        <p class="mt-3 text-slate-300 text-sm sm:text-base text-balance">
          Nhấp vào các trạng thái cảm xúc để quan sát đôi mắt robot biến đổi trên màn hình CRT ảo, hoặc nhấp vào các câu thoại mẫu để nghe thử giọng nói tiếng Việt mượt mà!
        </p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        <!-- Virtual Monitor -->
        <div class="lg:col-span-6 flex flex-col items-center">
          <div class="w-full max-w-md p-6 glass-card rounded-3xl border border-white/15 shadow-2xl relative">
            <div class="flex items-center justify-between pb-3 mb-3 border-b border-white/10 text-xs font-mono text-slate-400">
              <span class="flex items-center gap-2">
                <span class="h-2 w-2 rounded-full bg-cyan-400 animate-pulse"></span>
                <span id="sim-status-label" class="text-cyan-300 font-bold uppercase">待命 • STANDBY</span>
              </span>
              <div class="flex items-center gap-3">
                <span id="sim-wifi-icon">📶 WI-FI</span>
                <span>🔋 100%</span>
              </div>
            </div>

            <!-- Display Form Factor Switcher -->
            <div class="flex items-center gap-1.5 p-1 bg-black/40 border border-white/10 rounded-xl mb-4 text-[11px] font-mono">
              <button id="btn-mode-18" onclick="setDisplayMode('18landscape')" class="flex-1 py-1.5 px-2 rounded-lg bg-cyan-500/20 text-cyan-300 font-semibold border border-cyan-500/40 transition-all flex items-center justify-center gap-1.5">
                <span>🖥️ 1.8" Ngang (160x128)</span>
              </button>
              <button id="btn-mode-round" onclick="setDisplayMode('round')" class="flex-1 py-1.5 px-2 rounded-lg text-slate-400 hover:text-white transition-all flex items-center justify-center gap-1.5">
                <span>🐾 1.28" Tròn (240x240)</span>
              </button>
            </div>

            <div class="flex justify-center my-2">
              <div id="sim-screen-container" class="crt-screen w-full aspect-[5/4] max-w-[340px] rounded-2xl flex flex-col items-center justify-center p-6 relative overflow-hidden transition-all duration-500 border-4 border-slate-700/80 shadow-glow-cyan">
                <div class="absolute top-3 left-4 right-4 flex items-center justify-between text-[11px] font-mono text-cyan-400/70 z-20">
                  <span id="screen-status-badge">Musedy S3 • Online</span>
                  <span id="screen-fps">30.2 FPS</span>
                </div>

                <div id="robot-eyes-svg" class="w-48 h-32 flex items-center justify-center gap-6 z-20 transition-all duration-300">
                  <div id="eye-left" class="w-12 h-24 bg-gradient-to-b from-cyan-300 via-sky-400 to-blue-500 rounded-full shadow-[0_0_25px_#00F0FF] transition-all duration-300 transform"></div>
                  <div id="eye-right" class="w-12 h-24 bg-gradient-to-b from-cyan-300 via-sky-400 to-blue-500 rounded-full shadow-[0_0_25px_#00F0FF] transition-all duration-300 transform"></div>
                </div>

                <div id="audio-waveform" class="absolute bottom-4 flex items-center justify-center gap-1.5 z-20 opacity-0 transition-opacity duration-300">
                  <span class="w-1 bg-cyan-400 rounded-full animate-wave" style="animation-delay: 0.1s"></span>
                  <span class="w-1 bg-cyan-300 rounded-full animate-wave" style="animation-delay: 0.3s"></span>
                  <span class="w-1 bg-sky-400 rounded-full animate-wave" style="animation-delay: 0.5s"></span>
                  <span class="w-1 bg-blue-400 rounded-full animate-wave" style="animation-delay: 0.2s"></span>
                  <span class="w-1 bg-cyan-400 rounded-full animate-wave" style="animation-delay: 0.4s"></span>
                  <span class="w-1 bg-sky-300 rounded-full animate-wave" style="animation-delay: 0.6s"></span>
                  <span class="w-1 bg-cyan-400 rounded-full animate-wave" style="animation-delay: 0.2s"></span>
                </div>

                <div id="sim-subtitle" class="absolute bottom-2 px-4 py-1 rounded bg-black/60 text-xs font-medium text-cyan-200 text-center max-w-[90%] z-20 opacity-0 transition-opacity duration-300"></div>
              </div>
            </div>

            <div class="mt-4 pt-3 border-t border-white/10 flex items-center justify-between text-xs font-mono text-slate-400">
              <span id="sim-spec-label" class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-cyan-400"></span> 1.8" LANDSCAPE 160x128 (ST7735 / ST7789)</span>
              <span id="sim-ratio-label" class="text-cyan-400 font-bold">16-BIT RGB565 • 5:4 RATIO</span>
            </div>
          </div>
        </div>

        <!-- Controls -->
        <div class="lg:col-span-6 flex flex-col space-y-6">
          <div class="glass-card p-5 rounded-2xl border border-white/10">
            <h3 class="text-xs font-mono text-cyan-400 uppercase tracking-wider mb-3 text-balance">1. Chọn Biểu Cảm Của Robot:</h3>
            <div class="grid grid-cols-3 sm:grid-cols-5 gap-2">
              <button onclick="setEmotion('standby')" class="emotion-btn active px-2 sm:px-3 py-2.5 rounded-xl border border-cyan-500/40 bg-cyan-500/20 text-xs font-medium text-cyan-300 hover:bg-cyan-500/30 transition-all text-center min-h-[44px] flex items-center justify-center">
                待命 (Chờ)
              </button>
              <button onclick="setEmotion('happy')" class="emotion-btn px-2 sm:px-3 py-2.5 rounded-xl border border-white/10 bg-slate-800/40 text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-cyan-300 transition-all text-center min-h-[44px] flex items-center justify-center">
                😊 Vui Vẻ
              </button>
              <button onclick="setEmotion('listening')" class="emotion-btn px-2 sm:px-3 py-2.5 rounded-xl border border-white/10 bg-slate-800/40 text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-cyan-300 transition-all text-center min-h-[44px] flex items-center justify-center">
                🎧 Lắng Nghe
              </button>
              <button onclick="setEmotion('speaking')" class="emotion-btn px-2 sm:px-3 py-2.5 rounded-xl border border-white/10 bg-slate-800/40 text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-cyan-300 transition-all text-center min-h-[44px] flex items-center justify-center">
                🗣️ Đang Nói
              </button>
              <button onclick="setEmotion('thinking')" class="emotion-btn px-2 sm:px-3 py-2.5 rounded-xl border border-white/10 bg-slate-800/40 text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-cyan-300 transition-all text-center min-h-[44px] flex items-center justify-center">
                🤔 Suy Nghĩ
              </button>
            </div>
          </div>

          <div class="glass-card p-5 rounded-2xl border border-white/10">
            <h3 class="text-xs font-mono text-cyan-400 uppercase tracking-wider mb-3 text-balance">2. Nghe Thử Giọng Nói Tiếng Việt (Edge/Google TTS):</h3>
            <div class="flex flex-col space-y-2.5">
              <div class="p-3 rounded-xl border border-white/10 bg-slate-800/40 flex items-center justify-between gap-3">
                <div class="truncate text-xs text-slate-200">
                  <span class="text-cyan-400 font-semibold font-mono mr-1">#01</span> "Xin chào! Mình là robot Musedy S3!"
                </div>
                <button onclick="speakText('Xin chào! Mình là robot Musedy phiên bản máy tính cổ điển!')" 
                        class="phrase-btn shrink-0 px-3 py-1.5 rounded-lg border border-cyan-500/40 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 font-mono font-bold text-xs flex items-center gap-1.5 transition-all min-h-[36px]">
                  <span>▶ Phát</span>
                </button>
              </div>

              <div class="p-3 rounded-xl border border-white/10 bg-slate-800/40 flex items-center justify-between gap-3">
                <div class="truncate text-xs text-slate-200">
                  <span class="text-cyan-400 font-semibold font-mono mr-1">#02</span> "Hôm nay thời tiết thế nào, Musedy ơi?"
                </div>
                <button onclick="speakText('Hôm nay thời tiết thế nào, Musedy ơi?')" 
                        class="phrase-btn shrink-0 px-3 py-1.5 rounded-lg border border-cyan-500/40 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 font-mono font-bold text-xs flex items-center gap-1.5 transition-all min-h-[36px]">
                  <span>▶ Phát</span>
                </button>
              </div>

              <div class="p-3 rounded-xl border border-white/10 bg-slate-800/40 flex items-center justify-between gap-3">
                <div class="truncate text-xs text-slate-200">
                  <span class="text-cyan-400 font-semibold font-mono mr-1">#03</span> "Đang kết nối Wi-Fi &amp; cập nhật dữ liệu."
                </div>
                <button onclick="speakText('Đang kết nối Wi-Fi và cập nhật dữ liệu firmware mới nhất.')" 
                        class="phrase-btn shrink-0 px-3 py-1.5 rounded-lg border border-cyan-500/40 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 font-mono font-bold text-xs flex items-center gap-1.5 transition-all min-h-[36px]">
                  <span>▶ Phát</span>
                </button>
              </div>
            </div>

            <div class="mt-4 pt-4 border-t border-white/10">
              <label for="custom-speech-input" class="text-xs font-mono text-slate-400 block mb-2">Hoặc nhập câu bất kỳ để Musedy phát âm thanh:</label>
              <div class="flex items-center gap-2">
                <input id="custom-speech-input" type="text" placeholder="Nhập câu tiếng Việt hoặc tiếng Anh..." 
                       class="flex-1 px-3.5 py-2.5 rounded-xl bg-black/60 border border-white/15 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 min-h-[44px]">
                <button onclick="speakCustom()" 
                        class="px-5 py-2.5 rounded-xl border border-cyan-500/40 bg-cyan-500/20 text-cyan-300 font-bold text-xs hover:bg-cyan-500/30 active:scale-95 transition-all min-h-[44px] shrink-0">
                  Phát Âm
                </button>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </section>

  <!-- QUICK SHORTCUT CARDS TO WIRING & DEPLOYMENT -->
  <section class="py-16 border-t border-white/10 bg-black/40">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        
        <!-- Wiring Card -->
        <a href="wiring.html" class="glass-card p-6 sm:p-8 rounded-3xl border border-white/10 group hover:border-cyan-400/50 transition-all flex flex-col justify-between">
          <div>
            <div class="w-12 h-12 rounded-2xl bg-cyan-400/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 mb-5 group-hover:scale-110 transition-transform">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
            </div>
            <span class="text-xs font-mono text-cyan-400 uppercase tracking-wider">HARDWARE PINOUT &amp; CIRCUIT</span>
            <h3 class="text-2xl font-bold text-white mt-1 mb-2 text-balance">Sơ Đồ Kết Nối Phần Cứng Trực Quan</h3>
            <p class="text-slate-300 text-sm leading-relaxed text-balance">
              Xem chi tiết sơ đồ chân GPIO của ESP32-S3 kết nối tới Màn hình tròn GC9A01, Micro INMP441, Khuếch đại MAX98357A và cảm biến MPU6050 kèm bảng màu dây chuẩn.
            </p>
          </div>
          <div class="mt-6 pt-4 border-t border-white/10 flex items-center justify-between text-xs font-mono text-cyan-300">
            <span>BẢNG TRA CỨU ĐI DÂY CHI TIẾT</span>
            <span class="group-hover:translate-x-1 transition-transform">Mở Sơ Đồ →</span>
          </div>
        </a>

        <!-- Deploy Card -->
        <a href="deploy.html" class="glass-card p-6 sm:p-8 rounded-3xl border border-white/10 group hover:border-sky-400/50 transition-all flex flex-col justify-between">
          <div>
            <div class="w-12 h-12 rounded-2xl bg-sky-400/10 border border-sky-500/30 flex items-center justify-center text-sky-400 mb-5 group-hover:scale-110 transition-transform">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
            </div>
            <span class="text-xs font-mono text-sky-400 uppercase tracking-wider">ESP-IDF &amp; FIRMWARE FLASH</span>
            <h3 class="text-2xl font-bold text-white mt-1 mb-2 text-balance">Hướng Dẫn Triển Khai &amp; Nạp Firmware</h3>
            <p class="text-slate-300 text-sm leading-relaxed text-balance">
              Cẩm nang từng bước cấu hình Kconfig, biên dịch mã nguồn, nạp vào ESP32-S3 qua cổng Serial/JTAG, cấu hình Wi-Fi BLE và các lệnh điều khiển chẩn đoán CLI.
            </p>
          </div>
          <div class="mt-6 pt-4 border-t border-white/10 flex items-center justify-between text-xs font-mono text-sky-300">
            <span>HƯỚNG DẪN TỪNG BƯỚC</span>
            <span class="group-hover:translate-x-1 transition-transform">Xem Cẩm Nang →</span>
          </div>
        </a>

      </div>
    </div>
  </section>

  <!-- BENTO GRID ARCHITECTURE (Meta Astryx System) -->
  <section id="features" data-od-id="features-section" class="py-20 md:py-28 relative">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      
      <div class="text-center max-w-3xl mx-auto mb-16">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-cyan-500/30 bg-cyan-950/40 text-cyan-300 text-xs font-mono tracking-wider mb-3">
          SYSTEM ARCHITECTURE &amp; CAPABILITIES
        </div>
        <h2 class="text-3xl sm:text-4xl font-extrabold text-white tracking-tight text-balance">
          Hệ Thống Phần Cứng &amp; Tính Năng Đột Phá
        </h2>
        <p class="mt-3 text-slate-300 text-sm sm:text-base text-balance">
          Được thiết kế tối ưu từng milimét cho khả năng tản nhiệt tự nhiên, âm học dội sàn và đàm thoại thời gian thực.
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

        <div class="glass-card p-6 rounded-3xl border border-white/10 flex flex-col justify-between group h-full">
          <div>
            <div class="w-12 h-12 rounded-2xl bg-cyan-400/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 mb-5">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
            </div>
            <span class="text-xs font-mono text-cyan-400 uppercase tracking-wider">MAKERWORLD #1967811</span>
            <h3 class="text-xl font-bold text-white mt-1 mb-2 text-balance">Vỏ Máy Tính Retro (Musedy Edition)</h3>
            <p class="text-slate-300 text-sm leading-relaxed">
              Thiết kế nguyên mẫu bởi 董老爺 với thân vỏ Xanh Dương cổ điển, mặt trước trắng kem, khe đút đĩa mềm floppy, lỗ mắt camera và 4 phím cơ xúc giác trên đỉnh.
            </p>
          </div>
          <div class="mt-6 pt-4 border-t border-white/10 flex items-center justify-between text-xs font-mono text-slate-400">
            <span>KÍCH THƯỚC: 68.5 x 77.7 x 44.3 mm</span>
            <span class="text-cyan-400">3 CHI TIẾT STL</span>
          </div>
        </div>

        <div class="glass-card p-6 rounded-3xl border border-white/10 flex flex-col justify-between group h-full">
          <div>
            <div class="w-12 h-12 rounded-2xl bg-sky-400/10 border border-sky-500/30 flex items-center justify-center text-sky-400 mb-5">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
            </div>
            <span class="text-xs font-mono text-sky-400 uppercase tracking-wider">1.8" LANDSCAPE ADAPTER</span>
            <h3 class="text-xl font-bold text-white mt-1 mb-2 text-balance">Ngàm Màn Hình 1.8" Xoay Ngang (160x128)</h3>
            <p class="text-slate-300 text-sm leading-relaxed">
              Tấm ngàm chuyển đổi thông minh <code class="text-cyan-300 text-xs">musedy_computer_18_adapter.scad</code> và file STL lắp lọt khít màn hình 1.8" TFT 160x128 ST7735 vào hốc cửa sổ 44.9mm của vỏ máy tính retro, mang lại tỷ lệ hiển thị ngang 5:4 hoàn hảo!
            </p>
          </div>
          <div class="mt-6 pt-4 border-t border-white/10 flex items-center justify-between text-xs font-mono text-slate-400">
            <span>IN NHANH: ~18 PHÚT (~6G)</span>
            <span class="text-sky-400">KHỚP 100% CỬA SỔ</span>
          </div>
        </div>

        <div class="glass-card p-6 rounded-3xl border border-white/10 flex flex-col justify-between group h-full">
          <div>
            <div class="w-12 h-12 rounded-2xl bg-blue-400/10 border border-blue-500/30 flex items-center justify-center text-blue-400 mb-5">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path></svg>
            </div>
            <span class="text-xs font-mono text-blue-400 uppercase tracking-wider">ZERO-TOKEN TTS</span>
            <h3 class="text-xl font-bold text-white mt-1 mb-2 text-balance">Giọng Nói Tiếng Việt Miễn Phí</h3>
            <p class="text-slate-300 text-sm leading-relaxed">
              Tích hợp công nghệ Edge TTS &amp; Google Translate TTS trực tiếp trong firmware: Không tốn chi phí token phát âm, không cần API key trả phí, hỗ trợ song ngữ Anh - Việt mượt mà.
            </p>
          </div>
          <div class="mt-6 pt-4 border-t border-white/10 flex items-center justify-between text-xs font-mono text-slate-400">
            <span>CHI PHÍ VẬN HÀNH: 0 ĐỒNG</span>
            <span class="text-blue-400">TỰ ĐỘNG CHUNKING</span>
          </div>
        </div>

        <div class="glass-card p-6 rounded-3xl border border-white/10 flex flex-col justify-between group h-full">
          <div>
            <div class="w-12 h-12 rounded-2xl bg-emerald-400/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-5">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
            </div>
            <span class="text-xs font-mono text-emerald-400 uppercase tracking-wider">LOW LATENCY VAD</span>
            <h3 class="text-xl font-bold text-white mt-1 mb-2 text-balance">Voice Wakeup &amp; Ngắt Lời (Barge-in)</h3>
            <p class="text-slate-300 text-sm leading-relaxed">
              Thuật toán nhận diện giọng nói VAD và Wakeup từ khóa ("Rody ơi" / "Musedy") trên vi xử lý ESP32-S3. Hỗ trợ ngắt lời tức thì khi người dùng lên tiếng trong lúc robot đang nói.
            </p>
          </div>
          <div class="mt-6 pt-4 border-t border-white/10 flex items-center justify-between text-xs font-mono text-slate-400">
            <span>MIC: INMP441 I2S OMNI</span>
            <span class="text-emerald-400">BARGE-IN SUPPORT</span>
          </div>
        </div>

        <div class="glass-card p-6 rounded-3xl border border-white/10 flex flex-col justify-between group h-full">
          <div>
            <div class="w-12 h-12 rounded-2xl bg-amber-400/10 border border-amber-500/30 flex items-center justify-center text-amber-400 mb-5">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"></path></svg>
            </div>
            <span class="text-xs font-mono text-amber-400 uppercase tracking-wider">ACOUSTIC SUSPENSION</span>
            <h3 class="text-xl font-bold text-white mt-1 mb-2 text-balance">Âm Thanh Vòm &amp; Loa Hộp 3W</h3>
            <p class="text-slate-300 text-sm leading-relaxed">
              Mạch khuếch đại Class-D MAX98357A kết hợp loa từ tính trong buồng kín. Âm thanh thoát qua khe đáy 360°, dội vào mặt bàn tạo âm trầm ấm, rõ ràng, không bị rè méo.
            </p>
          </div>
          <div class="mt-6 pt-4 border-t border-white/10 flex items-center justify-between text-xs font-mono text-slate-400">
            <span>CÔNG SUẤT: 3W RMS (4Ω)</span>
            <span class="text-amber-400">BUỒNG KÍN CHỐNG SHORT</span>
          </div>
        </div>

        <div class="glass-card p-6 rounded-3xl border border-white/10 flex flex-col justify-between group h-full">
          <div>
            <div class="w-12 h-12 rounded-2xl bg-rose-400/10 border border-rose-500/30 flex items-center justify-center text-rose-400 mb-5">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"></path></svg>
            </div>
            <span class="text-xs font-mono text-rose-400 uppercase tracking-wider">MOTION &amp; SENSING</span>
            <h3 class="text-xl font-bold text-white mt-1 mb-2 text-balance">Cảm Biến 6-DOF &amp; Chạm Điện Dung</h3>
            <p class="text-slate-300 text-sm leading-relaxed">
              Cảm biến gia tốc MPU6050 nhận biết khi robot bị nghiêng, rung lắc hay rơi; cảm ứng chạm điện dung nhạy bén giúp người dùng vuốt chạm đỉnh đầu để tương tác cảm xúc.
            </p>
          </div>
          <div class="mt-6 pt-4 border-t border-white/10 flex items-center justify-between text-xs font-mono text-slate-400">
            <span>GIA TỐC: MPU6050 I2C</span>
            <span class="text-rose-400">CHẠM: GPIO 2</span>
          </div>
        </div>

      </div>

    </div>
  </section>

  <!-- DUAL MODEL SHOWCASE: RETRO COMPUTER VS ASTRO-POD -->
  <section id="hardware" data-od-id="hardware-section" class="py-20 border-t border-white/10 bg-astryx-subtle/40">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      
      <div class="text-center max-w-3xl mx-auto mb-12">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-sky-500/30 bg-sky-950/40 text-sky-300 text-xs font-mono tracking-wider mb-3">
          CHOOSE YOUR FORM FACTOR
        </div>
        <h2 class="text-3xl sm:text-4xl font-extrabold text-white tracking-tight text-balance">
          Hai Phong Cách Vỏ In 3D Hoàn Chỉnh
        </h2>
        <p class="mt-3 text-slate-300 text-sm sm:text-base text-balance">
          Cả hai mẫu vỏ đều đã có file 3D CAD tham số và test dung sai 100% tương thích với bo mạch Musedy S3.
        </p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        <!-- Model 1: Retro Computer -->
        <div class="glass-card rounded-3xl p-6 border-2 border-cyan-500/50 relative overflow-hidden flex flex-col justify-between h-full">
          <div class="absolute top-4 right-4 px-3 py-1 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 text-xs font-mono font-bold">
            BẢN IN CỦA BẠN (MÀU XANH)
          </div>
          <div>
            <h3 class="text-2xl font-bold text-white mb-1 text-balance">Mẫu 1: Máy Tính Cổ Điển Musedy AI</h3>
            <p class="text-xs font-mono text-slate-400 mb-4">THIẾT KẾ: 董老爺 (Mr. Dong) • MAKERWORLD #1967811</p>
            
            <div class="rounded-2xl overflow-hidden mb-5 bg-black/50 border border-white/10">
              <img src="data:image/png;base64,{b64_blue}" alt="Musedy AI Computer Blue" class="w-full h-64 object-cover object-center">
            </div>

            <ul class="space-y-2 text-sm text-slate-300 mb-6 font-mono text-xs">
              <li class="flex items-center gap-2">
                <span class="text-cyan-400">✔</span>
                <span>Thân máy xanh dương + mặt bezel trắng CRT + khe đĩa mềm</span>
              </li>
              <li class="flex items-center gap-2">
                <span class="text-cyan-400">✔</span>
                <span>Hỗ trợ cả màn hình tròn 1.28" (qua adapter) lẫn vuông 2.0" ST7789</span>
              </li>
              <li class="flex items-center gap-2">
                <span class="text-cyan-400">✔</span>
                <span>4 phím bấm cứng trên đỉnh, khoét cổng sạc Type-C bên hông</span>
              </li>
              <li class="flex items-center gap-2">
                <span class="text-cyan-400">✔</span>
                <span>File in 3D có sẵn trong thư mục: <code>Computer/</code></span>
              </li>
            </ul>
          </div>

          <div class="pt-4 border-t border-white/10 flex items-center justify-between">
            <span class="text-xs font-mono text-slate-400">3 File STL: 2.1 MB</span>
            <a href="https://makerworld.com/en/models/1967811-xiaozhi-ai-computer-xiaozhi#profileId-2115633" target="_blank" rel="noopener noreferrer" 
               class="px-4 py-2 rounded-xl border border-cyan-500/40 bg-cyan-500/10 text-cyan-300 font-bold text-xs hover:bg-cyan-500/20 active:scale-95 transition-all">
              Xem MakerWorld →
            </a>
          </div>
        </div>

        <!-- Model 2: Astro-Pod Capsule -->
        <div class="glass-card rounded-3xl p-6 border border-white/10 relative overflow-hidden flex flex-col justify-between h-full">
          <div>
            <h3 class="text-2xl font-bold text-white mb-1 text-balance">Mẫu 2: Quả Cầu Astro-Pod &amp; Tai Mecha</h3>
            <p class="text-xs font-mono text-slate-400 mb-4">THIẾT KẾ: MUSEDY-S3-ENC-V1 • NGUYÊN KHỐI OPENSCAD</p>
            
            <div class="rounded-2xl overflow-hidden mb-5 bg-black/50 border border-white/10">
              <img src="data:image/png;base64,{b64_astro}" alt="Musedy S3 Astro-Pod" class="w-full h-64 object-cover object-center">
            </div>

            <ul class="space-y-2 text-sm text-slate-300 mb-6 font-mono text-xs">
              <li class="flex items-center gap-2">
                <span class="text-sky-400">✔</span>
                <span>Vỏ cầu vát nghiêng 65° tối ưu góc nhìn khi đặt trên bàn</span>
              </li>
              <li class="flex items-center gap-2">
                <span class="text-sky-400">✔</span>
                <span>Ngàm nam châm N52 gắn tai thú cưng tháo rời (Modular Mecha Ears)</span>
              </li>
              <li class="flex items-center gap-2">
                <span class="text-sky-400">✔</span>
                <span>Vòng dẫn sáng Halo Ring hắt gầm đổi màu theo cảm xúc</span>
              </li>
              <li class="flex items-center gap-2">
                <span class="text-sky-400">✔</span>
                <span>File OpenSCAD tham số đầy đủ: <code>cad/rody_s3_astropod.scad</code></span>
              </li>
            </ul>
          </div>

          <div class="pt-4 border-t border-white/10 flex items-center justify-between">
            <span class="text-xs font-mono text-slate-400">4 Chi tiết: Bezel, Shell, Base, Ears</span>
            <span class="text-sky-400 font-mono text-xs">Tham Số 100% SCAD</span>
          </div>
        </div>

      </div>

    </div>
  </section>

  <!-- STL FILES & SPECIFICATIONS TABLE -->
  <section id="specs" data-od-id="specs-section" class="py-20 relative">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      
      <div class="text-center max-w-3xl mx-auto mb-12">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-cyan-500/30 bg-cyan-950/40 text-cyan-300 text-xs font-mono tracking-wider mb-3">
          FABRICATION &amp; MECHANICAL BOM
        </div>
        <h2 class="text-3xl sm:text-4xl font-extrabold text-white tracking-tight text-balance">
          Danh Mục File In 3D &amp; Dung Sai Cơ Khí
        </h2>
        <p class="mt-3 text-slate-300 text-sm sm:text-base text-balance">
          Mọi chi tiết đều đã được biên dịch và chạy qua bài kiểm tra dung sai tự động trong bộ test suite.
        </p>
      </div>

      <div class="glass-card rounded-2xl overflow-hidden border border-white/10">
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs font-mono">
            <thead class="bg-white/5 border-b border-white/10 text-slate-400 uppercase tracking-wider">
              <tr>
                <th class="px-6 py-4">Tên File</th>
                <th class="px-6 py-4">Kích Thước (Dx x Dy x Dz)</th>
                <th class="px-6 py-4">Vật Liệu Đề Xuất</th>
                <th class="px-6 py-4">Cài Đặt Cắt Lớp (Slicer)</th>
                <th class="px-6 py-4">Trạng Thái Test</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/5 text-slate-300">
              <tr class="hover:bg-slate-800/40 transition-colors">
                <td class="px-6 py-4 font-bold text-white flex items-center gap-2">
                  <span class="w-2 h-2 rounded-full bg-cyan-400"></span>
                  obj_2_Object_1.stl (Mặt trước trắng)
                </td>
                <td class="px-6 py-4">68.50 x 77.75 x 18.96 mm</td>
                <td class="px-6 py-4 text-slate-200">PLA+ / Resin Trắng Sữa</td>
                <td class="px-6 py-4">Layer 0.12mm, Infill 100%</td>
                <td class="px-6 py-4 text-emerald-400 font-bold">✓ PASSED (0.2mm Margin)</td>
              </tr>
              <tr class="hover:bg-slate-800/40 transition-colors">
                <td class="px-6 py-4 font-bold text-white flex items-center gap-2">
                  <span class="w-2 h-2 rounded-full bg-sky-400"></span>
                  obj_3_Object_4.stl (Thân máy xanh)
                </td>
                <td class="px-6 py-4">68.50 x 76.11 x 44.33 mm</td>
                <td class="px-6 py-4 text-slate-200">PETG / PLA+ Xanh Dương</td>
                <td class="px-6 py-4">Layer 0.16mm, Infill 25% Gyroid</td>
                <td class="px-6 py-4 text-emerald-400 font-bold">✓ PASSED (Type-C Slot)</td>
              </tr>
              <tr class="hover:bg-slate-800/40 transition-colors">
                <td class="px-6 py-4 font-bold text-white flex items-center gap-2">
                  <span class="w-2 h-2 rounded-full bg-blue-400"></span>
                  obj_1_组合体.stl (4 Nút bấm đỉnh)
                </td>
                <td class="px-6 py-4">46.45 x 11.50 x 10.00 mm</td>
                <td class="px-6 py-4 text-slate-200">PLA+ Tím / Xanh Navy</td>
                <td class="px-6 py-4">Layer 0.12mm, Infill 100%</td>
                <td class="px-6 py-4 text-emerald-400 font-bold">✓ PASSED (Friction Fit)</td>
              </tr>
              <tr class="hover:bg-slate-800/40 transition-colors bg-cyan-950/30">
                <td class="px-6 py-4 font-bold text-cyan-300 flex items-center gap-2">
                  <span class="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
                  musedy_computer_18_adapter.scad (Ngàm 1.8" Landscape)
                </td>
                <td class="px-6 py-4">48.40 x 48.00 x 3.40 mm</td>
                <td class="px-6 py-4 text-slate-200">PLA+ / Resin Trắng Kem</td>
                <td class="px-6 py-4">Layer 0.12mm, Infill 100%</td>
                <td class="px-6 py-4 text-emerald-400 font-bold">✓ PASSED (ST7735 160x128)</td>
              </tr>
              <tr class="hover:bg-slate-800/40 transition-colors bg-slate-900/30">
                <td class="px-6 py-4 font-medium text-slate-300 flex items-center gap-2">
                  <span class="w-2 h-2 rounded-full bg-slate-400"></span>
                  xiaozhi_gc9a01_adapter.scad (Ngàm GC9A01 Tròn)
                </td>
                <td class="px-6 py-4">48.40 x 48.00 x 3.40 mm</td>
                <td class="px-6 py-4 text-slate-200">PLA+ / Resin Trắng Kem</td>
                <td class="px-6 py-4">Layer 0.12mm, Infill 100%</td>
                <td class="px-6 py-4 text-emerald-400 font-bold">✓ PASSED (GC9A01 38.2mm)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>
  </section>

  <!-- QUICK TERMINAL COMMANDS -->
  <section data-od-id="commands-section" class="py-16 border-t border-white/10 bg-black/60 font-mono text-xs">
    <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="glass-card rounded-2xl p-6 border border-white/10">
        <div class="flex items-center justify-between pb-3 mb-4 border-b border-white/10 text-slate-400">
          <span class="flex items-center gap-2">
            <span class="w-3 h-3 rounded-full bg-rose-500 inline-block"></span>
            <span class="w-3 h-3 rounded-full bg-amber-500 inline-block"></span>
            <span class="w-3 h-3 rounded-full bg-emerald-400 inline-block"></span>
            <span class="ml-2 text-white font-bold">LỆNH THI CÔNG &amp; TEST NHANH TRÊN MÁY</span>
          </span>
          <span class="text-cyan-400">BASH / ZSH</span>
        </div>

        <div class="space-y-4">
          <div>
            <div class="text-slate-400 mb-1"># 1. Chạy toàn bộ 174 bài test tự động (bao gồm dung sai vỏ máy tính):</div>
            <div class="p-3 rounded-xl bg-black border border-white/10 text-cyan-300 select-all flex justify-between items-center">
              <code>DEVELOPER_DIR=/Library/Developer/CommandLineTools ./test_host.sh</code>
            </div>
          </div>
          <div>
            <div class="text-slate-400 mb-1"># 2. Xuất file STL ngàm chuyển đổi màn hình tròn GC9A01:</div>
            <div class="p-3 rounded-xl bg-black border border-white/10 text-sky-300 select-all flex justify-between items-center">
              <code>openscad -o cad/stl/xiaozhi_gc9a01_adapter.stl -D '$fn=96' cad/xiaozhi_gc9a01_adapter.scad</code>
            </div>
          </div>
          <div>
            <div class="text-slate-400 mb-1"># 3. Nạp firmware ESP32-S3 cho bo mạch Musedy S3:</div>
            <div class="p-3 rounded-xl bg-black border border-white/10 text-blue-300 select-all flex justify-between items-center">
              <code>idf.py -p /dev/cu.usbmodem1101 flash monitor</code>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>

  {SHARED_FOOTER}

  <!-- INTERACTIVE SIMULATOR SCRIPT -->
  <script>
    const eyeLeft = document.getElementById('eye-left');
    const eyeRight = document.getElementById('eye-right');
    const statusLabel = document.getElementById('sim-status-label');
    const screenStatus = document.getElementById('screen-status-badge');
    const waveform = document.getElementById('audio-waveform');
    const subtitle = document.getElementById('sim-subtitle');
    const emotionBtns = document.querySelectorAll('.emotion-btn');
    const screenContainer = document.getElementById('sim-screen-container');
    const specLabel = document.getElementById('sim-spec-label');
    const ratioLabel = document.getElementById('sim-ratio-label');
    const btn18 = document.getElementById('btn-mode-18');
    const btnRound = document.getElementById('btn-mode-round');

    let currentEmotion = 'standby';

    function setDisplayMode(mode) {{
      if (mode === '18landscape') {{
        screenContainer.className = "crt-screen w-full aspect-[5/4] max-w-[340px] rounded-2xl flex flex-col items-center justify-center p-6 relative overflow-hidden transition-all duration-500 border-4 border-slate-700/80 shadow-glow-cyan";
        specLabel.innerHTML = '<span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-cyan-400"></span> 1.8" LANDSCAPE 160x128 (ST7735 / ST7789)</span>';
        ratioLabel.textContent = "16-BIT RGB565 • 5:4 RATIO";
        btn18.className = "flex-1 py-1.5 px-2 rounded-lg bg-cyan-500/20 text-cyan-300 font-semibold border border-cyan-500/40 transition-all flex items-center justify-center gap-1.5";
        btnRound.className = "flex-1 py-1.5 px-2 rounded-lg text-slate-400 hover:text-white transition-all flex items-center justify-center gap-1.5";
      }} else {{
        screenContainer.className = "crt-screen w-64 h-64 sm:w-72 sm:h-72 rounded-full flex flex-col items-center justify-center p-6 relative overflow-hidden transition-all duration-500 border-4 border-slate-700/80 shadow-glow-cyan";
        specLabel.innerHTML = '<span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-emerald-400"></span> 1.28" ROUND 240x240 (GC9A01 SPI)</span>';
        ratioLabel.textContent = "16-BIT RGB565 • 1:1 CIRCLE";
        btnRound.className = "flex-1 py-1.5 px-2 rounded-lg bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/40 transition-all flex items-center justify-center gap-1.5";
        btn18.className = "flex-1 py-1.5 px-2 rounded-lg text-slate-400 hover:text-white transition-all flex items-center justify-center gap-1.5";
      }}
    }}

    function setEmotion(emotion) {{
      currentEmotion = emotion;
      emotionBtns.forEach(btn => btn.classList.remove('active', 'border-cyan-500/40', 'bg-cyan-500/20', 'text-cyan-300'));
      const activeBtn = Array.from(emotionBtns).find(b => b.getAttribute('onclick')?.includes(emotion));
      if (activeBtn) {{
        activeBtn.classList.add('active', 'border-cyan-500/40', 'bg-cyan-500/20', 'text-cyan-300');
      }}

      eyeLeft.className = "w-12 h-24 bg-gradient-to-b from-cyan-300 via-sky-400 to-blue-500 rounded-full shadow-[0_0_25px_#00F0FF] transition-all duration-300 transform";
      eyeRight.className = "w-12 h-24 bg-gradient-to-b from-cyan-300 via-sky-400 to-blue-500 rounded-full shadow-[0_0_25px_#00F0FF] transition-all duration-300 transform";
      waveform.classList.add('opacity-0');

      if (emotion === 'standby') {{
        statusLabel.textContent = "待命 • STANDBY";
        screenStatus.textContent = "Musedy S3 • Standby";
      }} else if (emotion === 'happy') {{
        statusLabel.textContent = "VUI VẺ • HAPPY";
        screenStatus.textContent = "Musedy S3 • Happy 😊";
        eyeLeft.className += " scale-y-50 rounded-b-none border-t-8 border-cyan-200 -rotate-12 translate-y-2";
        eyeRight.className += " scale-y-50 rounded-b-none border-t-8 border-cyan-200 rotate-12 translate-y-2";
      }} else if (emotion === 'listening') {{
        statusLabel.textContent = "LẮNG NGHE • LISTENING";
        screenStatus.textContent = "Musedy S3 • Listening 🎧";
        eyeLeft.className = "w-14 h-26 bg-cyan-300 rounded-full shadow-[0_0_35px_#00F0FF] scale-110 transition-all duration-300";
        eyeRight.className = "w-14 h-26 bg-cyan-300 rounded-full shadow-[0_0_35px_#00F0FF] scale-110 transition-all duration-300";
      }} else if (emotion === 'speaking') {{
        statusLabel.textContent = "ĐANG NÓI • SPEAKING";
        screenStatus.textContent = "Musedy S3 • Speaking 🗣️";
        waveform.classList.remove('opacity-0');
        eyeLeft.className += " scale-y-75";
        eyeRight.className += " scale-y-75";
      }} else if (emotion === 'thinking') {{
        statusLabel.textContent = "SUY NGHĨ • THINKING";
        screenStatus.textContent = "Musedy S3 • Thinking 🤔";
        eyeLeft.className = "w-10 h-20 bg-gradient-to-b from-sky-300 via-blue-500 to-indigo-600 rounded-full shadow-[0_0_30px_#2563EB] transition-all duration-300 -translate-y-2";
        eyeRight.className = "w-10 h-20 bg-gradient-to-b from-sky-300 via-blue-500 to-indigo-600 rounded-full shadow-[0_0_30px_#2563EB] transition-all duration-300 translate-y-2";
      }}
    }}

    function speakText(text) {{
      setEmotion('speaking');
      subtitle.textContent = text;
      subtitle.classList.remove('opacity-0');

      if ('speechSynthesis' in window) {{
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'vi-VN';
        utterance.rate = 1.05;
        utterance.pitch = 1.1;

        utterance.onend = () => {{
          waveform.classList.add('opacity-0');
          setTimeout(() => {{
            subtitle.classList.add('opacity-0');
            setEmotion('standby');
          }}, 1200);
        }};

        utterance.onerror = () => {{
          waveform.classList.add('opacity-0');
          setEmotion('standby');
        }};

        window.speechSynthesis.speak(utterance);
      }} else {{
        setTimeout(() => {{
          waveform.classList.add('opacity-0');
          subtitle.classList.add('opacity-0');
          setEmotion('standby');
        }}, 3500);
      }}
    }}

    function speakCustom() {{
      const input = document.getElementById('custom-speech-input');
      const val = input.value.trim();
      if (val) {{
        speakText(val);
      }}
    }}

    document.getElementById('custom-speech-input').addEventListener('keydown', (e) => {{
      if (e.key === 'Enter') speakCustom();
    }});

    setInterval(() => {{
      if (currentEmotion === 'standby') {{
        eyeLeft.style.transform = 'scaleY(0.1)';
        eyeRight.style.transform = 'scaleY(0.1)';
        setTimeout(() => {{
          eyeLeft.style.transform = '';
          eyeRight.style.transform = '';
        }}, 180);
      }}
    }}, 4000);
  </script>
</body>
</html>
'''

def generate_wiring_html():
    return f'''<!DOCTYPE html>
<html lang="vi" class="scroll-smooth">
<head>
  {SHARED_HEAD}
  <title>Sơ Đồ Kết Nối Phần Cứng • Musedy S3 (Hardware Pinout)</title>
  <meta name="description" content="Sơ đồ kết nối phần cứng và bảng chân GPIO chi tiết cho Robot Musedy S3: ESP32-S3, GC9A01 1.28, INMP441, MAX98357A, MPU6050.">
</head>
<body class="astryx-mesh astryx-grid min-h-screen antialiased selection:bg-cyan-500 selection:text-black">
  {NAV_HEADER}

  <!-- PAGE HERO -->
  <section class="py-12 md:py-16 border-b border-white/10 bg-black/40">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center gap-2 text-xs font-mono text-cyan-400 mb-3">
        <a href="index.html" class="hover:underline">Musedy.S3</a>
        <span>/</span>
        <span class="text-slate-400">Hardware Documentation</span>
      </div>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-white tracking-tight text-balance">
        Sơ Đồ Kết Nối Phần Cứng &amp; Pinout Musedy S3
      </h1>
      <p class="mt-3 text-slate-300 text-sm sm:text-base max-w-3xl text-balance">
        Tài liệu đấu nối dây tín hiệu chi tiết giữa vi điều khiển <strong>ESP32-S3 N16R8</strong> với màn hình tròn GC9A01, micro thu âm INMP441, ampli MAX98357A và cảm biến 6-DOF MPU6050.
      </p>

      <!-- Quick Action Badges -->
      <div class="flex flex-wrap items-center gap-3 pt-6">
        <a href="https://github.com/tody-agent/musedy/blob/main/docs/WIRING_DIAGRAM.md" target="_blank" rel="noopener noreferrer"
           class="px-4 py-2 rounded-xl bg-cyan-400 text-black font-bold text-xs hover:bg-cyan-300 transition-all flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
          Xem File Markdown (WIRING_DIAGRAM.md)
        </a>
        <a href="deploy.html"
           class="px-4 py-2 rounded-xl border border-white/20 bg-slate-800/40 text-white font-medium text-xs hover:border-cyan-400/50 hover:text-cyan-300 transition-all">
          Xem Hướng Dẫn Nạp Firmware →
        </a>
      </div>
    </div>
  </section>

  <!-- INTERACTIVE CIRCUIT PINOUT MATRIX -->
  <section class="py-16">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      
      <!-- Component Pin Cards Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
        
        <!-- Card 1: Display -->
        <div class="glass-card p-6 rounded-3xl border border-white/10 flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between pb-3 mb-4 border-b border-white/10">
              <span class="flex items-center gap-2 text-cyan-400 font-bold text-sm">
                <span class="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
                1. MÀN HÌNH 1.8" TFT 160x128 XOAY NGANG (ST7735 / ST7789 SPI)
              </span>
              <span class="text-xs font-mono text-slate-400">40MHz SPI</span>
            </div>
            <table class="w-full text-xs font-mono">
              <thead class="text-slate-400 border-b border-white/5">
                <tr><th class="py-2">Chân 1.8" TFT / GC9A01</th><th>Chân ESP32-S3</th><th>Màu Dây</th></tr>
              </thead>
              <tbody class="divide-y divide-white/5 text-slate-300">
                <tr><td class="py-2 font-bold text-white">VCC</td><td class="text-cyan-400">3.3V (hoặc 5V)</td><td>Đỏ</td></tr>
                <tr><td class="py-2 font-bold text-white">GND</td><td class="text-cyan-400">GND</td><td>Đen</td></tr>
                <tr><td class="py-2 font-bold text-white">SCK / SCL</td><td class="text-cyan-400 font-bold">GPIO 42</td><td>Vàng</td></tr>
                <tr><td class="py-2 font-bold text-white">SDA / MOSI</td><td class="text-cyan-400 font-bold">GPIO 41</td><td>Xanh lá</td></tr>
                <tr><td class="py-2 font-bold text-white">A0 / DC</td><td class="text-cyan-400 font-bold">GPIO 40</td><td>Cam</td></tr>
                <tr><td class="py-2 font-bold text-white">RESET / RES</td><td class="text-cyan-400 font-bold">GPIO 39</td><td>Trắng</td></tr>
                <tr><td class="py-2 font-bold text-white">CS</td><td class="text-cyan-400 font-bold">GPIO 38</td><td>Xanh dương</td></tr>
                <tr><td class="py-2 font-bold text-white">LED / BLK (PWM)</td><td class="text-cyan-400 font-bold">GPIO 21</td><td>Tím</td></tr>
              </tbody>
            </table>
          </div>
          <div class="mt-4 pt-3 border-t border-white/10 text-[11px] text-slate-400">
            * Module 1.8" TFT 8 chân (ST7735 / ST7789) dùng chung sơ đồ chân SPI với màn hình tròn GC9A01. Firmware Musedy tự động xoay ngang 160x128.
          </div>
        </div>

        <!-- Card 2: Microphone -->
        <div class="glass-card p-6 rounded-3xl border border-white/10 flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between pb-3 mb-4 border-b border-white/10">
              <span class="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                <span class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
                2. MICROPHONE I2S INMP441 (OMNIDIRECTIONAL)
              </span>
              <span class="text-xs font-mono text-slate-400">I2S0 RX</span>
            </div>
            <table class="w-full text-xs font-mono">
              <thead class="text-slate-400 border-b border-white/5">
                <tr><th class="py-2">Chân INMP441</th><th>Chân ESP32-S3</th><th>Màu Dây</th></tr>
              </thead>
              <tbody class="divide-y divide-white/5 text-slate-300">
                <tr><td class="py-2 font-bold text-white">VDD</td><td class="text-emerald-400">3.3V (Sạch)</td><td>Đỏ</td></tr>
                <tr><td class="py-2 font-bold text-white">GND</td><td class="text-emerald-400">GND</td><td>Đen</td></tr>
                <tr><td class="py-2 font-bold text-white">SD (Data Out)</td><td class="text-emerald-400 font-bold">GPIO 6</td><td>Vàng</td></tr>
                <tr><td class="py-2 font-bold text-white">WS (Word Select)</td><td class="text-emerald-400 font-bold">GPIO 4</td><td>Xanh lá</td></tr>
                <tr><td class="py-2 font-bold text-white">SCK (Bit Clock)</td><td class="text-emerald-400 font-bold">GPIO 5</td><td>Cam</td></tr>
                <tr><td class="py-2 font-bold text-white">L/R (Left/Right)</td><td class="text-emerald-400 font-bold">Nối GND</td><td>Đen (Kênh Trái)</td></tr>
              </tbody>
            </table>
          </div>
          <div class="mt-4 pt-3 border-t border-white/10 text-[11px] text-slate-400">
            * Bọc kín khe hở quanh micro bằng keo B-7000 để chống tiếng hú dội từ loa.
          </div>
        </div>

        <!-- Card 3: Amplifier & Speaker -->
        <div class="glass-card p-6 rounded-3xl border border-white/10 flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between pb-3 mb-4 border-b border-white/10">
              <span class="flex items-center gap-2 text-amber-400 font-bold text-sm">
                <span class="w-2.5 h-2.5 rounded-full bg-amber-400"></span>
                3. KHUẾCH ĐẠI MAX98357A &amp; LOA HỘP 3W
              </span>
              <span class="text-xs font-mono text-slate-400">I2S1 TX</span>
            </div>
            <table class="w-full text-xs font-mono">
              <thead class="text-slate-400 border-b border-white/5">
                <tr><th class="py-2">Chân MAX98357A</th><th>Chân ESP32 / Nguồn</th><th>Màu Dây</th></tr>
              </thead>
              <tbody class="divide-y divide-white/5 text-slate-300">
                <tr><td class="py-2 font-bold text-white">VIN</td><td class="text-amber-400 font-bold">5V (VBUS USB)</td><td>Đỏ to (Đạt 3W)</td></tr>
                <tr><td class="py-2 font-bold text-white">GND</td><td class="text-amber-400 font-bold">GND</td><td>Đen to</td></tr>
                <tr><td class="py-2 font-bold text-white">DIN</td><td class="text-amber-400 font-bold">GPIO 7</td><td>Vàng</td></tr>
                <tr><td class="py-2 font-bold text-white">BCLK</td><td class="text-amber-400 font-bold">GPIO 15</td><td>Cam</td></tr>
                <tr><td class="py-2 font-bold text-white">LRC</td><td class="text-amber-400 font-bold">GPIO 16</td><td>Xanh lá</td></tr>
                <tr><td class="py-2 font-bold text-white">SPK+ / SPK-</td><td class="text-amber-400">Loa 4Ω 3W</td><td>Đỏ / Đen</td></tr>
              </tbody>
            </table>
          </div>
          <div class="mt-4 pt-3 border-t border-white/10 text-[11px] text-slate-400">
            * Nối chân GAIN xuống GND để đặt gain chuẩn 9dB, âm trong trẻo không bị vỡ tiếng.
          </div>
        </div>

        <!-- Card 4: IMU & Touch -->
        <div class="glass-card p-6 rounded-3xl border border-white/10 flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between pb-3 mb-4 border-b border-white/10">
              <span class="flex items-center gap-2 text-rose-400 font-bold text-sm">
                <span class="w-2.5 h-2.5 rounded-full bg-rose-400"></span>
                4. CẢM BIẾN MPU6050 &amp; CẢM ỨNG CHẠM
              </span>
              <span class="text-xs font-mono text-slate-400">I2C0 &amp; TOUCH</span>
            </div>
            <table class="w-full text-xs font-mono">
              <thead class="text-slate-400 border-b border-white/5">
                <tr><th class="py-2">Chân Linh Kiện</th><th>Chân ESP32-S3</th><th>Chức Năng</th></tr>
              </thead>
              <tbody class="divide-y divide-white/5 text-slate-300">
                <tr><td class="py-2 font-bold text-white">MPU6050 SDA</td><td class="text-rose-400 font-bold">GPIO 8</td><td>I2C Data</td></tr>
                <tr><td class="py-2 font-bold text-white">MPU6050 SCL</td><td class="text-rose-400 font-bold">GPIO 9</td><td>I2C Clock</td></tr>
                <tr><td class="py-2 font-bold text-white">Lá nhôm chạm đỉnh</td><td class="text-rose-400 font-bold">GPIO 2</td><td>Cảm ứng điện dung</td></tr>
                <tr><td class="py-2 font-bold text-white">Nút BOOT / Talk</td><td class="text-rose-400 font-bold">GPIO 0</td><td>Bấm giữ nói chuyện</td></tr>
                <tr><td class="py-2 font-bold text-white">Nút Menu phụ</td><td class="text-rose-400 font-bold">GPIO 47</td><td>Cài đặt nhanh</td></tr>
              </tbody>
            </table>
          </div>
          <div class="mt-4 pt-3 border-t border-white/10 text-[11px] text-slate-400">
            * MPU6050 đặt ngang phẳng ở đáy để đọc chuẩn góc nghiêng 3 trục X/Y/Z.
          </div>
        </div>

      </div>

      <!-- Checklist Before Power On -->
      <div class="glass-card p-6 rounded-2xl border border-white/10">
        <h3 class="text-white font-bold text-base mb-4 flex items-center gap-2">
          <span class="text-emerald-400">✔</span> Checklist Kiểm Tra An Toàn Trước Khi Bật Nguồn
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono text-slate-300">
          <div class="flex items-start gap-2">
            <span class="text-cyan-400 font-bold">[1]</span>
            <span>Đo thông mạch VCC (3.3V) và 5V KHÔNG bị chập với GND.</span>
          </div>
          <div class="flex items-start gap-2">
            <span class="text-cyan-400 font-bold">[2]</span>
            <span>Chân L/R của module INMP441 đã hàn chắc chắn xuống GND.</span>
          </div>
          <div class="flex items-start gap-2">
            <span class="text-cyan-400 font-bold">[3]</span>
            <span>Dây tín hiệu I2S loa và micro đi tách biệt, không bó xoắn chung.</span>
          </div>
          <div class="flex items-start gap-2">
            <span class="text-cyan-400 font-bold">[4]</span>
            <span>Chân VIN của MAX98357A lấy trực tiếp từ nguồn 5V VBUS.</span>
          </div>
        </div>
      </div>

    </div>
  </section>

  {SHARED_FOOTER}
</body>
</html>
'''

def generate_deploy_html():
    return f'''<!DOCTYPE html>
<html lang="vi" class="scroll-smooth">
<head>
  {SHARED_HEAD}
  <title>Cẩm Nang Triển Khai &amp; Nạp Firmware • Musedy S3 (Deployment Guide)</title>
  <meta name="description" content="Hướng dẫn từng bước biên dịch và nạp firmware cho robot Musedy S3 bằng ESP-IDF, Kconfig, cấu hình Wi-Fi BLE và chẩn đoán CLI.">
</head>
<body class="astryx-mesh astryx-grid min-h-screen antialiased selection:bg-cyan-500 selection:text-black">
  {NAV_HEADER}

  <!-- PAGE HERO -->
  <section class="py-12 md:py-16 border-b border-white/10 bg-black/40">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center gap-2 text-xs font-mono text-cyan-400 mb-3">
        <a href="index.html" class="hover:underline">Musedy.S3</a>
        <span>/</span>
        <span class="text-slate-400">Deployment Documentation</span>
      </div>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-white tracking-tight text-balance">
        Hướng Dẫn Triển Khai &amp; Nạp Firmware Musedy S3
      </h1>
      <p class="mt-3 text-slate-300 text-sm sm:text-base max-w-3xl text-balance">
        Quy trình chuẩn hóa từ sao chép mã nguồn, chạy 174 bài host test kiểm tra dung sai, cấu hình Kconfig, biên dịch và nạp firmware vào vi điều khiển <strong>ESP32-S3</strong>.
      </p>

      <div class="flex flex-wrap items-center gap-3 pt-6">
        <a href="https://github.com/tody-agent/musedy/blob/main/docs/DEPLOYMENT_GUIDE.md" target="_blank" rel="noopener noreferrer"
           class="px-4 py-2 rounded-xl bg-cyan-400 text-black font-bold text-xs hover:bg-cyan-300 transition-all flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
          Xem File Markdown (DEPLOYMENT_GUIDE.md)
        </a>
        <a href="wiring.html"
           class="px-4 py-2 rounded-xl border border-white/20 bg-slate-800/40 text-white font-medium text-xs hover:border-cyan-400/50 hover:text-cyan-300 transition-all">
          Xem Sơ Đồ Đi Dây Phần Cứng →
        </a>
      </div>
    </div>
  </section>

  <!-- STEP BY STEP DEPLOYMENT FLOW -->
  <section class="py-16">
    <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
      
      <!-- Step 1 -->
      <div class="glass-card p-6 sm:p-8 rounded-3xl border border-white/10">
        <div class="flex items-center gap-3 mb-4">
          <span class="w-8 h-8 rounded-xl bg-cyan-400/20 border border-cyan-400/40 text-cyan-300 font-mono font-bold flex items-center justify-center text-sm">
            01
          </span>
          <h2 class="text-xl font-bold text-white">Sao Chép Mã Nguồn &amp; Kiểm Thử Tự Động</h2>
        </div>
        <p class="text-sm text-slate-300 mb-4">
          Trước khi kết nối phần cứng, hãy chạy bộ 174 bài test tự động trên máy tính để đảm bảo môi trường và thuật toán VAD, Edge TTS và dung sai vỏ máy tính đều hoạt động hoàn hảo:
        </p>
        <div class="space-y-3 font-mono text-xs">
          <div class="p-3.5 rounded-xl bg-black border border-white/10 text-cyan-300 select-all">
            <code>git clone https://github.com/tody-agent/musedy.git &amp;&amp; cd musedy</code>
          </div>
          <div class="p-3.5 rounded-xl bg-black border border-white/10 text-sky-300 select-all">
            <code>DEVELOPER_DIR=/Library/Developer/CommandLineTools ./test_host.sh</code>
          </div>
        </div>
      </div>

      <!-- Step 2 -->
      <div class="glass-card p-6 sm:p-8 rounded-3xl border border-white/10">
        <div class="flex items-center gap-3 mb-4">
          <span class="w-8 h-8 rounded-xl bg-sky-400/20 border border-sky-400/40 text-sky-300 font-mono font-bold flex items-center justify-center text-sm">
            02
          </span>
          <h2 class="text-xl font-bold text-white">Chọn Cấu Hình Thiết Bị (Device Overlay)</h2>
        </div>
        <p class="text-sm text-slate-300 mb-4">
          Nạp cấu hình tối ưu sẵn cho Musedy S3 (mặc định màn hình 1.8" xoay ngang 160x128 ST7735 cho vỏ máy tính retro):
        </p>
        <div class="space-y-3 font-mono text-xs">
          <div class="p-3.5 rounded-xl bg-black border border-white/10 text-sky-300 select-all">
            <code>idf.py set-target esp32s3</code>
          </div>
          <div class="p-3.5 rounded-xl bg-black border border-white/10 text-sky-300 select-all">
            <code>cp devices/sdkconfig.muse-computer-18 sdkconfig   # Hoặc sdkconfig.muse-bread-s3</code>
          </div>
        </div>
      </div>

      <!-- Step 3 -->
      <div class="glass-card p-6 sm:p-8 rounded-3xl border border-white/10">
        <div class="flex items-center gap-3 mb-4">
          <span class="w-8 h-8 rounded-xl bg-blue-400/20 border border-blue-400/40 text-blue-300 font-mono font-bold flex items-center justify-center text-sm">
            03
          </span>
          <h2 class="text-xl font-bold text-white">Biên Dịch &amp; Nạp Firmware (Flash &amp; Monitor)</h2>
        </div>
        <p class="text-sm text-slate-300 mb-4">
          Cắm cáp Type-C kết nối ESP32-S3 với máy tính và thực hiện nạp:
        </p>
        <div class="space-y-3 font-mono text-xs">
          <div class="p-3.5 rounded-xl bg-black border border-white/10 text-blue-300 select-all">
            <code>idf.py build</code>
          </div>
          <div class="p-3.5 rounded-xl bg-black border border-white/10 text-emerald-300 select-all">
            <code>idf.py -p /dev/cu.usbmodem1101 flash monitor</code>
          </div>
        </div>
      </div>

      <!-- Step 4 -->
      <div class="glass-card p-6 sm:p-8 rounded-3xl border border-white/10">
        <div class="flex items-center gap-3 mb-4">
          <span class="w-8 h-8 rounded-xl bg-emerald-400/20 border border-emerald-400/40 text-emerald-300 font-mono font-bold flex items-center justify-center text-sm">
            04
          </span>
          <h2 class="text-xl font-bold text-white">Cấu Hình Wi-Fi &amp; Các Lệnh CLI Nhanh</h2>
        </div>
        <p class="text-sm text-slate-300 mb-4">
          Gửi lệnh qua cửa sổ Serial Monitor (115200 baud) để kích hoạt:
        </p>
        <div class="space-y-2.5 font-mono text-xs">
          <div class="p-3 rounded-xl bg-black/60 border border-white/10 flex justify-between items-center text-slate-300">
            <span>&gt;wifi=Ten_Wifi,Mat_Khau_Wifi</span>
            <span class="text-cyan-400 text-[11px]">Lưu mạng &amp; Kết nối</span>
          </div>
          <div class="p-3 rounded-xl bg-black/60 border border-white/10 flex justify-between items-center text-slate-300">
            <span>&gt;say=Xin chào! Mình là robot Musedy!</span>
            <span class="text-sky-400 text-[11px]">Phát âm tức thì qua loa</span>
          </div>
          <div class="p-3 rounded-xl bg-black/60 border border-white/10 flex justify-between items-center text-slate-300">
            <span>&gt;diag</span>
            <span class="text-emerald-400 text-[11px]">Báo cáo sức khỏe chip &amp; RAM</span>
          </div>
          <div class="p-3 rounded-xl bg-black/60 border border-white/10 flex justify-between items-center text-slate-300">
            <span>&gt;wakeup=on</span>
            <span class="text-amber-400 text-[11px]">Bật nhận diện giọng nói thường trực</span>
          </div>
        </div>
      </div>

    </div>
  </section>

  {SHARED_FOOTER}
</body>
</html>
'''

def main():
    print("=== Generating Musedy AI Pages ===")
    
    # Generate HTML content
    index_html = generate_index_html()
    wiring_html = generate_wiring_html()
    deploy_html = generate_deploy_html()

    # Write to root (for GitHub Pages root deployment)
    (ROOT / "index.html").write_text(index_html, encoding="utf-8")
    (ROOT / "wiring.html").write_text(wiring_html, encoding="utf-8")
    (ROOT / "deploy.html").write_text(deploy_html, encoding="utf-8")
    print("✓ Saved root pages: index.html, wiring.html, deploy.html")

    # Write to docs/ (for GitHub Pages docs/ deployment)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / "index.html").write_text(index_html, encoding="utf-8")
    (DOCS_DIR / "wiring.html").write_text(wiring_html, encoding="utf-8")
    (DOCS_DIR / "deploy.html").write_text(deploy_html, encoding="utf-8")
    print("✓ Saved docs/ pages: docs/index.html, docs/wiring.html, docs/deploy.html")

    # Copy to OpenDesign if project exists
    od_proj = Path("/Volumes/Builder/Design/.od/projects/rody-s3-astryx")
    if od_proj.exists():
        (od_proj / "index.html").write_text(index_html, encoding="utf-8")
        print("✓ Synced to OpenDesign studio project")

    print("=== All Pages Generated Successfully! ===")

if __name__ == "__main__":
    main()
