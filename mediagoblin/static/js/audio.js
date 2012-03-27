/**
 * GNU MediaGoblin -- federated, autonomous media hosting
 * Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

var audioPlayer = new Object();

(function (audioPlayer) {
    audioPlayer.init = function (audioElement) {
        audioPlayer.audioElement = audioElement;
        console.log(audioElement);
        attachEvents();
        $(audioElement).hide();
    };

    function attachEvents () {
        audioPlayer.audioElement.addEventListener('durationchange', audioPlayer.durationChange, true);
        audioPlayer.audioElement.addEventListener('timeupdate', audioPlayer.timeUpdate, true);
        audioPlayer.audioElement.addEventListener('progress', audioPlayer.onProgress, true);
        $(document).ready( function () {
            $('.audio-spectrogram').delegate('.seekbar', 'click', audioPlayer.onSeek);
            $('.audio-spectrogram').delegate('.audio-control-play-pause', 'click', audioPlayer.playPause);
        });
    }

    audioPlayer.onProgress = function(a, b, c) {
        console.log(a, b, c);
        buffered = audioPlayer.audioElement.buffered;

        ranges = new Array(); 

        for (i = 0; i < buffered.length; i++) {
            ranges[i] = new Array();
            ranges[i][0] = buffered.start(i);
            ranges[i][1] = buffered.end(i);
        }
        console.log('ranges', ranges);
        $('.audio-spectrogram .buffered').width(
            (ranges[0][1] / audioPlayer.audioElement.duration) * audioPlayer.imageElement.width());
    };

    audioPlayer.onSeek = function (e) {
        console.log('onSeek', e);
        im = audioPlayer.imageElement;
        pos = e.offsetX / im.width();
        audioPlayer.audioElement.currentTime = pos * audioPlayer.audioElement.duration;
        audioPlayer.audioElement.play();
        audioPlayer.setState(audioPlayer.PLAYING);
    };

    audioPlayer.playPause = function (e) {
        console.log('playPause', e);
        if (audioPlayer.audioElement.paused) {
            audioPlayer.audioElement.play();
            audioPlayer.setState(audioPlayer.PLAYING);
        } else {
            audioPlayer.audioElement.pause();
            audioPlayer.setState(audioPlayer.PAUSED);
        }
    };

    audioPlayer.NULL = null;
    audioPlayer.PLAYING = 2;
    audioPlayer.PAUSED = 4;

    audioPlayer.state = audioPlayer.NULL;

    audioPlayer.setState = function (state) {
        if (state == audioPlayer.state) {
            return;
        }

        switch (state) {
            case audioPlayer.PLAYING:
                $('.audio-spectrogram .audio-control-play-pause')
                    .removeClass('paused').addClass('playing')
                    .text('■');
                break;
            case audioPlayer.PAUSED:
                $('.audio-spectrogram .audio-control-play-pause')
                    .removeClass('playing').addClass('paused')
                    .text('▶');
                break;
        }
    };

    audioPlayer.durationChange = function () {
        duration = audioPlayer.audioElement.duration;
    };

    audioPlayer.timeUpdate = function () {
        currentTime = audioPlayer.audioElement.currentTime;
        playhead = audioPlayer.imageElement.parent().find('.playhead');
        playhead.css('width', (currentTime / audioPlayer.audioElement.duration) * audioPlayer.imageElement.width());
        time = formatTime(currentTime);
        duration = formatTime(audioPlayer.audioElement.duration);
        audioPlayer.imageElement.parent().find('.audio-currentTime').text(time + '/' + duration);
    };

    function formatTime(seconds) {
        var h = Math.floor(seconds / (60 * 60));
        var m = Math.floor((seconds - h * 60 * 60) / 60);
        var s = Math.round(seconds - h * 60 * 60 - m * 60);
        return '' + (h ? (h < 10 ? '0' + h : h) + ':' : '') + (m < 10 ? '0' + m : m) + ':' + (s < 10 ? '0' + s : s);
    }

    audioPlayer.attachToImage = function (imageElement) {
        /**
         * Attach the player to an image element
         */
        console.log(imageElement);
        im = $(imageElement);
        audioPlayer.imageElement = im;
        $('<div class="playhead"></div>').appendTo(im.parent());
        $('<div class="buffered"></div>').appendTo(im.parent());
        $('<div class="seekbar"></div>').appendTo(im.parent());
        $('<div class="audio-control-play-pause paused">▶</div>').appendTo(im.parent());
        $('<div class="audio-currentTime">00:00</div>').appendTo(im.parent());
    };
})(audioPlayer);

$(document).ready(function () {
    if (!$('.audio-media').length) {
        return;
    }

    console.log('Initializing audio player');

    audioElements = $('.audio-media .audio-player');
    audioPlayer.init(audioElements[0]);
    audioPlayer.attachToImage($('.audio-spectrogram img')[0]);
});

