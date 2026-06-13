// Interview session page — displays Q&A chat interface for text mode.
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile/features/interview/presentation/session/interview_session_bloc.dart';
import 'package:mobile/shared/models/interview_message.dart';

/// The main interview session page with chat bubbles and text input.
class InterviewSessionPage extends StatefulWidget {
  final String sessionId;

  const InterviewSessionPage({super.key, required this.sessionId});

  @override
  State<InterviewSessionPage> createState() => _InterviewSessionPageState();
}

class _InterviewSessionPageState extends State<InterviewSessionPage> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    context.read<InterviewSessionBloc>().add(InitializeSession(widget.sessionId));
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
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
        // Show error messages
        if (state.errorMessage != null) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(state.errorMessage!)),
          );
        }

        // Navigate to report polling page after completion
        if (state.isCompleted) {
          context.pushReplacement('/interview/report/${widget.sessionId}');
        }

        // Navigate home after cancellation
        if (state.isCancelled) {
          context.go('/home');
        }

        // Auto-scroll when messages change
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
              if (state.session?.status == 'in_progress' ||
                  state.messages.isNotEmpty &&
                      !state.isCompleted &&
                      !state.isCancelled)
                _buildInputArea(state),
            ],
          ),
        );
      },
    );
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
        );
      },
    );
  }

  Widget _buildInputArea(InterviewSessionState state) {
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
class _MessageBubble extends StatelessWidget {
  final InterviewMessage message;
  final bool showAvatar;

  const _MessageBubble({required this.message, required this.showAvatar});

  bool get _isInterviewer => message.role == 'interviewer';

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        mainAxisAlignment:
            _isInterviewer ? MainAxisAlignment.start : MainAxisAlignment.end,
        crossAxisAlignment:
            CrossAxisAlignment.start,
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
            child: Container(
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
