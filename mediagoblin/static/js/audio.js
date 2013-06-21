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
        audioPlayer.audioElement.addEventListener(
            'durationchange', audioPlayer.durationChange, true);
        audioPlayer.audioElement.addEventListener(
            'timeupdate', audioPlayer.timeUpdate, true);
        audioPlayer.audioElement.addEventListener(
            'progress', audioPlayer.onProgress, true);
        audioPlayer.audioElement.addEventListener(
            'ended', audioPlayer.onEnded, true);

        $(document).ready( function () {
            $('.audio-spectrogram').delegate(
                '.seekbar', 'click', audioPlayer.onSeek);
            $('.audio-spectrogram').delegate(
                '.audio-control-play-pause', 'click', audioPlayer.playPause);
            $('.audio-spectrogram').delegate(
                '.audio-volume', 'change', audioPlayer.onVolumeChange);
            $('.audio-media').delegate(
                '.audio-spectrogram', 'attachedControls',
                audioPlayer.onControlsAttached);
        });
    }

    audioPlayer.onVolumeChange = function(e) {
        console.log('volume change', e);
        audioPlayer.audioElement.volume = e.target.value;
    }

    audioPlayer.onControlsAttached = function(e) {
        console.log('Controls attached', e);
        $('.audio-spectrogram .audio-volume').val(
                Math.round(audioPlayer.audioElement.volume, 2));
    }

    audioPlayer.onProgress = function(e) {
        /**
         * Handler for file download progress
         */
        console.log(e);

        var buffered = audioPlayer.audioElement.buffered;

        ranges = new Array(); 

        var indicators = $('.audio-spectrogram .buffered-indicators div');

        for (var i = 0; i < buffered.length; i++) {
            if (!(i in indicators)) {
                $('<div style="display: none;"></div>')
                    .appendTo($('.audio-spectrogram .buffered-indicators'))
                    .fadeIn(500);
                indicators = $('.audio-spectrogram .buffered-indicators div');
            }
            var posStart = ((buffered.start(i) / audioPlayer.audioElement.duration)
                    * audioPlayer.imageElement.width());
            var posStop = ((buffered.end(i) / audioPlayer.audioElement.duration)
                    * audioPlayer.imageElement.width());
            console.log('indicators', indicators);

            var indicator = $(indicators[i]);

            indicator.css('left', posStart);
            indicator.css('width', posStop - posStart);
        }

        /*
         * Clean up unused indicators
         */
        if (indicators.length > buffered.length) {
            for (var i = buffered.length; i < indicators.length; i++) {
                $(indicators[i]).fadeOut(500, function () {
                    this.remove();
                });
            }
        }
    };

    audioPlayer.onSeek = function (e) {
        /**
         * Callback handler for seek event, which is a .click() event on the
         * .seekbar element
         */
        console.log('onSeek', e);

        var im = audioPlayer.imageElement;
        var pos = (e.offsetX || e.originalEvent.layerX) / im.width();

        audioPlayer.audioElement.currentTime = pos * audioPlayer.audioElement.duration;
        audioPlayer.audioElement.play();
        audioPlayer.setState(audioPlayer.PLAYING);
    };

    audioPlayer.onEnded = function (e) {
        audioPlayer.setState(audioPlayer.PAUSED);
    }

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
        } else {
            audioPlayer.state = state;
        }

        switch (state) {
            case audioPlayer.PLAYING:
                $('.audio-spectrogram .audio-control-play-pause')
                    .removeClass('paused').addClass('playing')
                    .text('▮▮');
                break;
            case audioPlayer.PAUSED:
                $('.audio-spectrogram .audio-control-play-pause')
                    .removeClass('playing').addClass('paused')
                    .text('▶');
                break;
        }
    };

    audioPlayer.durationChange = function () {
        // ???
    };

    audioPlayer.timeUpdate = function () {
        /**
         * Callback handler for the timeupdate event, responsible for
         * updating the playhead
         */
        var currentTime = audioPlayer.audioElement.currentTime;
        var playhead = audioPlayer.imageElement.parent().find('.playhead');
        playhead.css('width', (currentTime / audioPlayer.audioElement.duration)
                * audioPlayer.imageElement.width());
        var time = formatTime(currentTime);
        var duration = formatTime(audioPlayer.audioElement.duration);
        audioPlayer.imageElement.parent()
            .find('.audio-currentTime')
            .text(time + '/' + duration);
    };

    function formatTime(seconds) {
        /**
         * Format a time duration in (hh:)?mm:ss manner
         */
        var h = Math.floor(seconds / (60 * 60));
        var m = Math.floor((seconds - h * 60 * 60) / 60);
        var s = Math.round(seconds - h * 60 * 60 - m * 60);
        return '' + (h ? (h < 10 ? '0' + h : h) + ':' : '') + (m < 10 ? '0' + m : m) + ':' + (s < 10 ? '0' + s : s);
    }

    audioPlayer.formatTime = formatTime;

    audioPlayer.attachToImage = function (imageElement) {
        /**
         * Attach the player to an image element
         */
        console.log(imageElement);

        var im = $(imageElement);

        audioPlayer.imageElement = im;

        $('<div class="playhead"></div>').appendTo(im.parent());
        $('<div class="buffered-indicators"></div>').appendTo(im.parent());
        $('<div class="seekbar"></div>').appendTo(im.parent());
        $('<div class="audio-control-play-pause paused">▶</div>').appendTo(im.parent());
        $('<div class="audio-currentTime">00:00</div>').appendTo(im.parent());
        $('<input type="range" class="audio-volume"'
                +'value="1" min="0" max="1" step="0.001" />').appendTo(im.parent());
        $('.audio-spectrogram').trigger('attachedControls');
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
