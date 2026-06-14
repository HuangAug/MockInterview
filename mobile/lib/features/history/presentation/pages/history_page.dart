// History page — displays paginated interview history list.
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile/features/history/presentation/bloc/history_bloc.dart';
import 'package:mobile/features/history/presentation/bloc/history_event.dart';
import 'package:mobile/features/history/presentation/bloc/history_state.dart';
import 'package:mobile/shared/models/interview_session.dart';

class HistoryPage extends StatefulWidget {
  const HistoryPage({super.key});

  @override
  State<HistoryPage> createState() => _HistoryPageState();
}

class _HistoryPageState extends State<HistoryPage> {
  final _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    context.read<HistoryBloc>().add(LoadHistory());
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      final state = context.read<HistoryBloc>().state;
      if (state is HistoryLoaded && state.hasMore) {
        context.read<HistoryBloc>().add(LoadMoreHistory());
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('历史记录'),
        centerTitle: true,
      ),
      body: BlocBuilder<HistoryBloc, HistoryState>(
        builder: (context, state) {
          if (state is HistoryLoading) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state is HistoryError) {
            return _buildErrorView(context, state.message);
          }
          if (state is HistoryLoaded) {
            if (state.items.isEmpty) {
              return _buildEmptyView(context);
            }
            return _buildListView(context, state);
          }
          return const SizedBox.shrink();
        },
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: 1,
        onDestinationSelected: (index) {
          switch (index) {
            case 0:
              context.go('/home');
            case 1:
              break;
            case 2:
              context.go('/profile');
          }
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home),
            label: '首页',
          ),
          NavigationDestination(
            icon: Icon(Icons.history_outlined),
            selectedIcon: Icon(Icons.history),
            label: '历史',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outlined),
            selectedIcon: Icon(Icons.person),
            label: '我的',
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyView(BuildContext context) {
    return RefreshIndicator(
      onRefresh: () async {
        context.read<HistoryBloc>().add(RefreshHistory());
      },
      child: ListView(
        children: [
          SizedBox(
            height: MediaQuery.of(context).size.height * 0.6,
            child: const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.inbox, size: 64, color: Colors.grey),
                  SizedBox(height: 16),
                  Text(
                    '暂无面试记录',
                    style: TextStyle(fontSize: 16, color: Colors.grey),
                  ),
                  SizedBox(height: 8),
                  Text(
                    '完成一次面试后，记录会出现在这里',
                    style: TextStyle(fontSize: 13, color: Colors.grey),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorView(BuildContext context, String message) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.error_outline,
            size: 48,
            color: Theme.of(context).colorScheme.error,
          ),
          const SizedBox(height: 16),
          Text(message, style: const TextStyle(fontSize: 14)),
          const SizedBox(height: 16),
          FilledButton(
            onPressed: () =>
                context.read<HistoryBloc>().add(LoadHistory()),
            child: const Text('重试'),
          ),
        ],
      ),
    );
  }

  Widget _buildListView(BuildContext context, HistoryLoaded state) {
    return RefreshIndicator(
      onRefresh: () async {
        context.read<HistoryBloc>().add(RefreshHistory());
      },
      child: ListView.builder(
        controller: _scrollController,
        padding: const EdgeInsets.all(16),
        itemCount: state.items.length + (state.hasMore ? 1 : 0),
        itemBuilder: (context, index) {
          if (index >= state.items.length) {
            return const Padding(
              padding: EdgeInsets.all(16),
              child: Center(child: CircularProgressIndicator()),
            );
          }
          return _HistoryItemCard(
            item: state.items[index],
            onTap: () => _onItemTap(context, state.items[index]),
          );
        },
      ),
    );
  }

  void _onItemTap(BuildContext context, InterviewSessionListItem item) {
    if (item.status == 'in_progress') {
      context.push('/interview/session/${item.id}');
    } else if (item.status == 'completed' &&
        item.reportStatus == 'ready') {
      context.push('/interview/report/${item.id}');
    }
  }
}

class _HistoryItemCard extends StatelessWidget {
  final InterviewSessionListItem item;
  final VoidCallback onTap;

  const _HistoryItemCard({required this.item, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final canViewReport =
        item.status == 'completed' && item.reportStatus == 'ready';
    final isInProgress = item.status == 'in_progress';
    final isTappable = canViewReport || isInProgress;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: isTappable ? onTap : null,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            item.jobRoleName,
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                        _buildStatusChip(theme),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        _InfoChip(
                          icon: Icons.signal_cellular_alt,
                          label: _difficultyLabel(item.difficulty),
                        ),
                        const SizedBox(width: 12),
                        _InfoChip(
                          icon: item.mode == 'voice'
                              ? Icons.mic
                              : Icons.chat_bubble_outline,
                          label: item.mode == 'voice' ? '语音' : '文字',
                        ),
                        const SizedBox(width: 12),
                        _InfoChip(
                          icon: Icons.calendar_today,
                          label: _formatDate(item.createdAt),
                        ),
                      ],
                    ),
                    if (item.overallScore != null) ...[
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          const Icon(
                            Icons.emoji_events,
                            size: 16,
                            color: Color(0xFFF59E0B),
                          ),
                          const SizedBox(width: 4),
                          Text(
                            '${item.overallScore!.toStringAsFixed(1)} 分',
                            style: const TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                              color: Color(0xFFF59E0B),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
              if (isInProgress)
                Icon(
                  Icons.arrow_forward_ios,
                  size: 16,
                  color: theme.colorScheme.primary,
                )
              else if (canViewReport)
                Icon(
                  Icons.chevron_right,
                  size: 20,
                  color: Colors.grey.shade400,
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatusChip(ThemeData theme) {
    final (label, color) = switch (item.status) {
      'completed' => (
          item.reportStatus == 'ready' ? '已完成' : '报告生成中',
          item.reportStatus == 'ready'
              ? const Color(0xFF22C55E)
              : const Color(0xFFF59E0B)
        ),
      'in_progress' => ('进行中', const Color(0xFF3B82F6)),
      'cancelled' => ('已取消', Colors.grey),
      'failed' => ('失败', const Color(0xFFEF4444)),
      'pending' => ('待开始', Colors.grey),
      _ => ('未知', Colors.grey),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w500,
          color: color,
        ),
      ),
    );
  }

  String _difficultyLabel(String difficulty) {
    return switch (difficulty) {
      'junior' => '初级',
      'mid' => '中级',
      'senior' => '高级',
      _ => difficulty,
    };
  }

  String _formatDate(DateTime date) {
    return '${date.month}/${date.day} ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
  }
}

class _InfoChip extends StatelessWidget {
  final IconData icon;
  final String label;

  const _InfoChip({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: Colors.grey.shade600),
        const SizedBox(width: 4),
        Text(
          label,
          style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
        ),
      ],
    );
  }
}
