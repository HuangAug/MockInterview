/// VoiceInputWidget — hold-to-record button, transcription preview, and submit.
library;

import 'package:flutter/material.dart';
import 'package:mobile/core/audio/audio_service.dart';

class VoiceInputWidget extends StatefulWidget {
  final String sessionId;
  final AudioService audioService;
  final void Function(String text) onSubmit;
  final bool isSubmitting;

  const VoiceInputWidget({
    super.key,
    required this.sessionId,
    required this.audioService,
    required this.onSubmit,
    required this.isSubmitting,
  });

  @override
  State<VoiceInputWidget> createState() => _VoiceInputWidgetState();
}

class _VoiceInputWidgetState extends State<VoiceInputWidget> {
  bool _isRecording = false;
  String? _transcribedText;
  bool _isTranscribing = false;
  String? _error;
  final _textController = TextEditingController();

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  Future<void> _startRecording() async {
    setState(() {
      _error = null;
      _transcribedText = null;
      _textController.clear();
    });

    final hasPermission = await widget.audioService.canRecord;
    if (!hasPermission) {
      if (!mounted) return;
      setState(() => _error = '请授予麦克风权限后重试');
      return;
    }

    try {
      await widget.audioService.startRecording();
      if (!mounted) return;
      setState(() => _isRecording = true);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = '录音启动失败');
    }
  }

  Future<void> _stopRecording() async {
    try {
      final path = await widget.audioService.stopRecording();
      if (!mounted) return;
      setState(() => _isRecording = false);

      if (path == null) {
        setState(() => _error = '录音文件未找到');
        return;
      }

      setState(() => _isTranscribing = true);
      final text = await widget.audioService.transcribeAudio(
        widget.sessionId,
        path,
      );

      if (!mounted) return;
      setState(() {
        _transcribedText = text;
        _textController.text = text;
        _isTranscribing = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isRecording = false;
        _isTranscribing = false;
        _error = '转写失败，请重试';
      });
    }
  }

  void _submitTranscription() {
    final text = _textController.text.trim();
    if (text.isEmpty) return;
    widget.onSubmit(text);
    setState(() {
      _transcribedText = null;
      _textController.clear();
    });
  }

  void _cancelTranscription() {
    setState(() {
      _transcribedText = null;
      _textController.clear();
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 4,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: SafeArea(
        top: false,
        child: _buildContent(theme),
      ),
    );
  }

  Widget _buildContent(ThemeData theme) {
    // Error state
    if (_error != null) {
      return Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
          const SizedBox(height: 8),
          TextButton(
            onPressed: () => setState(() => _error = null),
            child: const Text('关闭'),
          ),
        ],
      );
    }

    // Transcribing state
    if (_isTranscribing) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
            SizedBox(width: 12),
            Text('正在转写语音...'),
          ],
        ),
      );
    }

    // Transcription preview — editable text + submit/cancel
    if (_transcribedText != null) {
      return Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextField(
            controller: _textController,
            decoration: InputDecoration(
              labelText: '转写结果（可编辑后提交）',
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              contentPadding: const EdgeInsets.all(12),
            ),
            maxLines: 4,
            minLines: 2,
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: widget.isSubmitting ? null : _cancelTranscription,
                  child: const Text('重新录音'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: FilledButton(
                  onPressed: widget.isSubmitting ? null : _submitTranscription,
                  child: Text(widget.isSubmitting ? '提交中...' : '提交回答'),
                ),
              ),
            ],
          ),
        ],
      );
    }

    // Submitting state (text mode submission in progress)
    if (widget.isSubmitting) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
            SizedBox(width: 12),
            Text('AI 正在思考...'),
          ],
        ),
      );
    }

    // Default — hold-to-record button
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          GestureDetector(
            onLongPressStart: (_) => _startRecording(),
            onLongPressEnd: (_) {
              if (_isRecording) _stopRecording();
            },
            onLongPressCancel: () {
              if (_isRecording) _stopRecording();
            },
            child: Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: _isRecording
                    ? theme.colorScheme.error
                    : theme.colorScheme.primary,
                boxShadow: [
                  BoxShadow(
                    color: (_isRecording
                            ? theme.colorScheme.error
                            : theme.colorScheme.primary)
                        .withValues(alpha: 0.3),
                    blurRadius: 12,
                    spreadRadius: 2,
                  ),
                ],
              ),
              child: Icon(
                _isRecording ? Icons.stop : Icons.mic,
                size: 36,
                color: Colors.white,
              ),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            _isRecording ? '松开结束录音' : '长按录音',
            style: theme.textTheme.bodySmall,
          ),
          if (_isRecording)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(
                '录音中...',
                style: TextStyle(
                  color: theme.colorScheme.error,
                  fontSize: 12,
                ),
              ),
            ),
        ],
      ),
    );
  }
}
