/// AudioService — manages microphone recording and TTS playback.
library;

import 'dart:io';

import 'package:audioplayers/audioplayers.dart';
import 'package:mobile/features/interview/data/interview_repository.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

class AudioService {
  final AudioRecorder _recorder = AudioRecorder();
  final AudioPlayer _player = AudioPlayer();
  final InterviewRepository _interviewRepository;

  AudioService({required this._interviewRepository});

  /// Whether microphone permission has been granted and recording is possible.
  Future<bool> get canRecord async {
    try {
      return await _recorder.hasPermission();
    } catch (_) {
      return false;
    }
  }

  /// Start recording audio to a temp file. Returns the file path.
  Future<String> startRecording() async {
    final dir = await getTemporaryDirectory();
    final ext = Platform.isIOS ? 'm4a' : 'webm';
    final path =
        '${dir.path}/mock_interview_${DateTime.now().millisecondsSinceEpoch}.$ext';

    await _recorder.start(
      const RecordConfig(
        encoder: AudioEncoder.aacLc,
        sampleRate: 44100,
        numChannels: 1,
      ),
      path: path,
    );
    return path;
  }

  /// Stop recording and return the path of the recorded file.
  Future<String?> stopRecording() async {
    return _recorder.stop();
  }

  /// Whether the recorder is currently active.
  Future<bool> get isRecording async {
    try {
      return await _recorder.isRecording();
    } catch (_) {
      return false;
    }
  }

  /// Upload a recorded audio file to the backend and return transcribed text.
  Future<String> transcribeAudio(String sessionId, String filePath) async {
    return _interviewRepository.transcribeAudio(sessionId, filePath);
  }

  /// Download TTS audio for an interviewer message and play it.
  Future<void> playTts(String sessionId, String messageId) async {
    try {
      final dir = await getTemporaryDirectory();
      final ttsDir = Directory('${dir.path}/tts_cache');
      if (!ttsDir.existsSync()) {
        ttsDir.createSync(recursive: true);
      }
      final localPath = '${ttsDir.path}/${sessionId}_$messageId.mp3';

      // Download if not cached locally
      if (!File(localPath).existsSync()) {
        await _interviewRepository.downloadTtsAudio(
          sessionId,
          messageId,
          localPath,
        );
      }

      await _player.stop();
      await _player.play(DeviceFileSource(localPath));
    } catch (_) {
      // TTS playback is non-critical; swallow errors silently.
    }
  }

  /// Stop any currently playing audio.
  Future<void> stopPlayback() async {
    await _player.stop();
  }

  /// Release all audio resources.
  Future<void> dispose() async {
    await _recorder.dispose();
    await _player.dispose();
  }
}
