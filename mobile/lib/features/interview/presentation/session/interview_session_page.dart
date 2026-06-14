// Interview session page — displays Q&A chat interface for text and voice modes.
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get_it/get_it.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile/core/audio/audio_service.dart';
import 'package:mobile/features/interview/presentation/session/interview_session_bloc.dart';
import 'package:mobile/features/interview/presentation/session/voice/voice_input_widget.dart';
import 'package:mobile/shared/models/interview_message.dart';

/// The main interview session page with chat bubbles and text/voice input.
class InterviewSessionPage extends StatefulWidget {
  final String sessionId;

  const InterviewSessionPage({super.key, required this.sessionId});

  @override
  State<InterviewSessionPage> createState() => _InterviewSessionPageState();
}

class _InterviewSessionPageState extends State<InterviewSessionPage> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  final AudioService _audioService = GetIt.I<AudioService>();

  /// Message IDs whose TTS has already been auto-played.
  final Set<String> _playedTtsIds = {};

  bool _isVoiceMode = false;

  @override
  void initState() {
    super.initState();
    context.read<InterviewSessionBloc>().add(InitializeSession(widget.sessionId));
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    _audioService.stopPlayback();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _sendMessage() {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    context.read<InterviewSessionBloc>().add(SubmitAnswer(text));
    _controller.clear();
  }

  /// Submit a transcribed voice answer.
  void _submitVoiceAnswer(String text) {
    context.read<InterviewSessionBloc>().add(SubmitAnswer(text));
  }

  /// Auto-play TTS for the latest interviewer message that hasn't been played.
  void _autoPlayTtsIfNeeded(List<InterviewMessage> messages) {
    if (!_isVoiceMode) return;

    // Find the last interviewer message
    for (final msg in messages.reversed) {
      if (msg.role == 'interviewer' && !_playedTtsIds.contains(msg.id)) {
        _playedTtsIds.add(msg.id);
        _audioService.playTts(widget.sessionId, msg.id);
        return;
      }
    }
  }

  Future<void> _showEndDialog() async {
    final bloc = context.read<InterviewSessionBloc>();
    final state = bloc.state;
    final questionCount = state.session?.questionCount ?? 0;

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('结束面试'),
        content: Text(
          questionCount > 0
              ? '确定结束面试吗？结束后将生成评估报告。'
              : '确定取消面试吗？',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('取消'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('确定'),
          ),
        ],
      ),
    );

    if (confirmed == true && mounted) {
      if (questionCount > 0) {
        bloc.add(CompleteInterview());
      } else {
        bloc.add(CancelInterview());
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return BlocConsumer<InterviewSessionBloc, InterviewSessionState>(
      listener: (context, state) {
        // Detect voice mode from session
        if (state.session != null) {
          _isVoiceMode = state.session!.mode == 'voice';
        }

        // Show error message
        if (state.errorMessage != null) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(state.errorMessage!)),
          );
        }

        // Navigate to report polling page after completion
        if (state.isCompleted) {
          _audioService.stopPlayback();
          context.pushReplacement('/interview/report/${widget.sessionId}');
        }

        // Navigate home after cancellation
        if (state.isCancelled) {
          _audioService.stopPlayback();
          context.go('/home');
        }

        // Auto-play TTS for voice mode and auto-scroll
        _autoPlayTtsIfNeeded(state.messages);
        _scrollToBottom();
      },
      builder: (context, state) {
        if (state.isLoading && state.session == null) {
          return Scaffold(
            appBar: AppBar(title: const Text('面试')),
            body: const Center(child: CircularProgressIndicator()),
          );
        }

        final session = state.session;
        final questionCount = session?.questionCount ?? 0;
        final maxQuestions = session?.maxQuestions ?? 8;

        return Scaffold(
          appBar: AppBar(
            title: Text('第 $questionCount/$maxQuestions 题'),
            centerTitle: true,
            actions: [
              IconButton(
                icon: const Icon(Icons.stop_circle_outlined),
                tooltip: '结束面试',
                onPressed: _showEndDialog,
              ),
            ],
          ),
          body: Column(
            children: [
              Expanded(child: _buildMessageList(state)),
              if (_shouldShowInput(state)) _buildInputArea(state),
            ],
          ),
        );
      },
    );
  }

  bool _shouldShowInput(InterviewSessionState state) {
    if (state.session?.status == 'in_progress') return true;
    if (state.messages.isNotEmpty && !state.isCompleted && !state.isCancelled) {
      return true;
    }
    return false;
  }

  Widget _buildMessageList(InterviewSessionState state) {
    if (state.messages.isEmpty) {
      return const Center(
        child: Text(
          '面试准备中...',
          style: TextStyle(color: Colors.grey, fontSize: 16),
        ),
      );
    }

    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.all(16),
      itemCount: state.messages.length,
      itemBuilder: (context, index) {
        final message = state.messages[index];
        return _MessageBubble(
          message: message,
          showAvatar: index == 0 ||
              state.messages[index - 1].role != message.role,
          isVoiceMode: _isVoiceMode,
          sessionId: widget.sessionId,
          audioService: _audioService,
        );
      },
    );
  }

  Widget _buildInputArea(InterviewSessionState state) {
    if (_isVoiceMode) {
      return VoiceInputWidget(
        sessionId: widget.sessionId,
        audioService: _audioService,
        onSubmit: _submitVoiceAnswer,
        isSubmitting: state.isSubmitting,
      );
    }

    final canSend =
        !state.isSubmitting && !state.isFinished && !state.isCompleted;

    return Container(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
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
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _controller,
                decoration: InputDecoration(
                  hintText: state.isSubmitting
                      ? 'AI 正在思考...'
                      : '输入你的回答...',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                  ),
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 12,
                  ),
                ),
                maxLines: 4,
                minLines: 1,
                enabled: canSend,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) {
                  if (canSend) _sendMessage();
                },
              ),
            ),
            const SizedBox(width: 8),
            if (state.isSubmitting)
              const SizedBox(
                width: 24,
                height: 24,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            else
              IconButton.filled(
                onPressed: canSend ? _sendMessage : null,
                icon: const Icon(Icons.send),
              ),
          ],
        ),
      ),
    );
  }
}

/// A single chat bubble — interviewer on the left, candidate on the right.
/// In voice mode, interviewer bubbles show a play button for TTS replay.
class _MessageBubble extends StatelessWidget {
  final InterviewMessage message;
  final bool showAvatar;
  final bool isVoiceMode;
  final String sessionId;
  final AudioService audioService;

  const _MessageBubble({
    required this.message,
    required this.showAvatar,
    required this.isVoiceMode,
    required this.sessionId,
    required this.audioService,
  });

  bool get _isInterviewer => message.role == 'interviewer';

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        mainAxisAlignment:
            _isInterviewer ? MainAxisAlignment.start : MainAxisAlignment.end,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (_isInterviewer) ...[
            if (showAvatar)
              CircleAvatar(
                radius: 16,
                backgroundColor: theme.colorScheme.primary,
                child: const Icon(Icons.person, size: 18, color: Colors.white),
              )
            else
              const SizedBox(width: 32),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Column(
              crossAxisAlignment:
                  _isInterviewer ? CrossAxisAlignment.start : CrossAxisAlignment.end,
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: _isInterviewer
                        ? theme.colorScheme.surfaceContainerHighest
                        : theme.colorScheme.primary,
                    borderRadius: BorderRadius.only(
                      topLeft: const Radius.circular(12),
                      topRight: const Radius.circular(12),
                      bottomLeft: Radius.circular(_isInterviewer ? 4 : 12),
                      bottomRight: Radius.circular(_isInterviewer ? 12 : 4),
                    ),
                  ),
                  child: Text(
                    message.content,
                    style: TextStyle(
                      color: _isInterviewer
                          ? theme.colorScheme.onSurface
                          : theme.colorScheme.onPrimary,
                    ),
                  ),
                ),
                // TTS replay button for interviewer messages in voice mode
                if (_isInterviewer && isVoiceMode)
                  Padding(
                    padding: const EdgeInsets.only(top: 2),
                    child: InkWell(
                      onTap: () => audioService.playTts(sessionId, message.id),
                      borderRadius: BorderRadius.circular(12),
                      child: Padding(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 4,
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              Icons.volume_up,
                              size: 14,
                              color: theme.colorScheme.primary,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              '播放',
                              style: TextStyle(
                                fontSize: 12,
                                color: theme.colorScheme.primary,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
          if (!_isInterviewer) ...[
            const SizedBox(width: 8),
            if (showAvatar)
              CircleAvatar(
                radius: 16,
                backgroundColor: theme.colorScheme.tertiary,
                child: const Icon(Icons.face, size: 18, color: Colors.white),
              )
            else
              const SizedBox(width: 32),
          ],
        ],
      ),
    );
  }
}
