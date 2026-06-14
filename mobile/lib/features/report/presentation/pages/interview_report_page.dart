// Interview report page — polls status then displays full report.
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile/features/report/presentation/bloc/report_bloc.dart';
import 'package:mobile/features/report/presentation/bloc/report_event.dart';
import 'package:mobile/features/report/presentation/bloc/report_state.dart';
import 'package:mobile/shared/models/interview_report.dart';

class InterviewReportPage extends StatefulWidget {
  final String sessionId;

  const InterviewReportPage({super.key, required this.sessionId});

  @override
  State<InterviewReportPage> createState() => _InterviewReportPageState();
}

class _InterviewReportPageState extends State<InterviewReportPage> {
  @override
  void initState() {
    super.initState();
    context.read<ReportBloc>().add(StartReportPolling(widget.sessionId));
  }

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<ReportBloc, ReportState>(
      builder: (context, state) {
        return Scaffold(
          appBar: AppBar(title: const Text('面试报告')),
          body: _buildBody(context, state),
        );
      },
    );
  }

  Widget _buildBody(BuildContext context, ReportState state) {
    if (state is ReportLoading || state is ReportPolling) {
      return _buildLoadingView(state);
    }
    if (state is ReportReady) {
      return _buildReportView(context, state.report);
    }
    if (state is ReportFailed) {
      return _buildFailedView(context, state.message);
    }
    return const SizedBox.shrink();
  }

  Widget _buildLoadingView(ReportState state) {
    final attempts = state is ReportPolling ? state.attempts : 0;
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const CircularProgressIndicator(),
          const SizedBox(height: 24),
          const Text(
            '报告生成中，请稍候...',
            style: TextStyle(fontSize: 16, color: Colors.grey),
          ),
          if (attempts > 0) ...[
            const SizedBox(height: 8),
            Text(
              '已等待 ${attempts * 2} 秒',
              style: const TextStyle(fontSize: 12, color: Colors.grey),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildFailedView(BuildContext context, String message) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.error_outline,
              size: 64,
              color: Theme.of(context).colorScheme.error,
            ),
            const SizedBox(height: 16),
            Text(
              message,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 32),
            FilledButton(
              onPressed: () => context.go('/home'),
              child: const Text('返回首页'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildReportView(BuildContext context, InterviewReport report) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _buildOverallScore(context, report.overallScore),
          const SizedBox(height: 24),
          _buildDimensionScores(context, report),
          const SizedBox(height: 24),
          _buildSection(
            context,
            title: '优点',
            items: report.strengths,
            icon: Icons.check_circle,
            color: const Color(0xFF22C55E),
          ),
          const SizedBox(height: 16),
          _buildSection(
            context,
            title: '不足',
            items: report.weaknesses,
            icon: Icons.warning_amber,
            color: const Color(0xFFEF4444),
          ),
          const SizedBox(height: 16),
          _buildSection(
            context,
            title: '建议',
            items: report.suggestions,
            icon: Icons.lightbulb,
            color: Theme.of(context).colorScheme.primary,
          ),
          const SizedBox(height: 24),
          _buildQuestionFeedback(context, report.questionFeedback),
          const SizedBox(height: 24),
          _buildSummary(context, report.summary),
          const SizedBox(height: 32),
          FilledButton.icon(
            onPressed: () => context.go('/home'),
            icon: const Icon(Icons.home),
            label: const Text('返回首页'),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  Widget _buildOverallScore(BuildContext context, double score) {
    final color = _scoreColor(score);
    return Center(
      child: Column(
        children: [
          SizedBox(
            width: 120,
            height: 120,
            child: Stack(
              fit: StackFit.expand,
              children: [
                CircularProgressIndicator(
                  value: score / 100,
                  strokeWidth: 10,
                  backgroundColor: Colors.grey.shade200,
                  valueColor: AlwaysStoppedAnimation(color),
                ),
                Center(
                  child: Text(
                    score.toStringAsFixed(1),
                    style: TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                      color: color,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '综合得分',
            style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
          ),
        ],
      ),
    );
  }

  Widget _buildDimensionScores(BuildContext context, InterviewReport report) {
    final dimensions = [
      _Dimension('沟通能力', report.communicationScore),
      _Dimension('技术能力', report.technicalScore),
      _Dimension('问题解决', report.problemSolvingScore),
      _Dimension('回答结构', report.structureScore),
    ];

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '维度评分',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 16),
            ...dimensions.map((d) => _buildDimensionBar(context, d)),
          ],
        ),
      ),
    );
  }

  Widget _buildDimensionBar(BuildContext context, _Dimension d) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          SizedBox(
            width: 80,
            child: Text(d.label, style: const TextStyle(fontSize: 14)),
          ),
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: d.score / 100,
                minHeight: 8,
                backgroundColor: Colors.grey.shade200,
                valueColor: AlwaysStoppedAnimation(_scoreColor(d.score)),
              ),
            ),
          ),
          const SizedBox(width: 8),
          SizedBox(
            width: 40,
            child: Text(
              d.score.toStringAsFixed(1),
              textAlign: TextAlign.end,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: _scoreColor(d.score),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSection(
    BuildContext context, {
    required String title,
    required List<String> items,
    required IconData icon,
    required Color color,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: color, size: 20),
                const SizedBox(width: 8),
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            ...items.map(
              (item) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('• ', style: TextStyle(color: color)),
                    Expanded(child: Text(item, style: const TextStyle(fontSize: 14))),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuestionFeedback(
    BuildContext context,
    List<QuestionFeedbackItem> feedback,
  ) {
    if (feedback.isEmpty) return const SizedBox.shrink();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '逐题反馈',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 12),
            ...feedback.map((f) => _buildFeedbackItem(context, f)),
          ],
        ),
      ),
    );
  }

  Widget _buildFeedbackItem(BuildContext context, QuestionFeedbackItem f) {
    return ExpansionTile(
      tilePadding: EdgeInsets.zero,
      title: Text(
        '第 ${f.sequence} 题: ${f.question}',
        maxLines: 2,
        overflow: TextOverflow.ellipsis,
        style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
      ),
      subtitle: Row(
        children: [
          Text(
            '得分: ${f.score.toStringAsFixed(1)}',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: _scoreColor(f.score),
            ),
          ),
        ],
      ),
      children: [
        Padding(
          padding: const EdgeInsets.only(left: 8, right: 8, bottom: 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '回答概要: ${f.answerSummary}',
                style: TextStyle(fontSize: 13, color: Colors.grey.shade700),
              ),
              const SizedBox(height: 8),
              Text(
                '改进建议: ${f.feedback}',
                style: const TextStyle(fontSize: 13),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildSummary(BuildContext context, String summary) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '总体评价',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 12),
            Text(summary, style: const TextStyle(fontSize: 14, height: 1.6)),
          ],
        ),
      ),
    );
  }

  Color _scoreColor(double score) {
    if (score >= 90) return const Color(0xFF22C55E);
    if (score >= 75) return const Color(0xFF3B82F6);
    if (score >= 60) return const Color(0xFFF59E0B);
    return const Color(0xFFEF4444);
  }
}

class _Dimension {
  final String label;
  final double score;
  _Dimension(this.label, this.score);
}
