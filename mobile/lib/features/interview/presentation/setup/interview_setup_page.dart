// InterviewSetupPage — select job role, difficulty, and mode before starting.
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile/features/interview/presentation/setup/interview_setup_bloc.dart';
import 'package:mobile/shared/models/job_role.dart';

class InterviewSetupPage extends StatefulWidget {
  const InterviewSetupPage({super.key});

  @override
  State<InterviewSetupPage> createState() => _InterviewSetupPageState();
}

class _InterviewSetupPageState extends State<InterviewSetupPage> {
  @override
  void initState() {
    super.initState();
    context.read<InterviewSetupBloc>().add(LoadJobRoles());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('面试设置')),
      body: BlocConsumer<InterviewSetupBloc, InterviewSetupState>(
        listener: (context, state) {
          if (state.createdSession != null) {
            context.pushReplacement(
              '/interview/session/${state.createdSession!.id}',
            );
          }
          if (state.errorMessage != null) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(state.errorMessage!)),
            );
          }
        },
        builder: (context, state) {
          if (state.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _buildSectionTitle('选择岗位'),
                const SizedBox(height: 12),
                _buildJobRoleGrid(context, state),
                const SizedBox(height: 24),
                _buildSectionTitle('选择难度'),
                const SizedBox(height: 12),
                _buildDifficultySelector(context, state),
                const SizedBox(height: 24),
                _buildSectionTitle('选择模式'),
                const SizedBox(height: 12),
                _buildModeSelector(context, state),
                const SizedBox(height: 32),
                _buildStartButton(context, state),
                const SizedBox(height: 16),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
    );
  }

  Widget _buildJobRoleGrid(BuildContext context, InterviewSetupState state) {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        childAspectRatio: 1.6,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
      ),
      itemCount: state.jobRoles.length,
      itemBuilder: (context, index) {
        final role = state.jobRoles[index];
        final isSelected = state.selectedJobRole?.id == role.id;
        return _JobRoleCard(
          role: role,
          isSelected: isSelected,
          onTap: () => context
              .read<InterviewSetupBloc>()
              .add(SelectJobRole(role)),
        );
      },
    );
  }

  Widget _buildDifficultySelector(
    BuildContext context,
    InterviewSetupState state,
  ) {
    const difficulties = [
      ('junior', '初级', '应届生/1年以内'),
      ('mid', '中级', '1-3年经验'),
      ('senior', '高级', '3年以上经验'),
    ];

    return SegmentedButton<String>(
      segments: difficulties
          .map((d) => ButtonSegment(
                value: d.$1,
                label: Text(d.$2),
              ))
          .toList(),
      selected: {state.selectedDifficulty ?? ''},
      onSelectionChanged: (selected) {
        context
            .read<InterviewSetupBloc>()
            .add(SelectDifficulty(selected.first));
      },
    );
  }

  Widget _buildModeSelector(BuildContext context, InterviewSetupState state) {
    return Row(
      children: [
        Expanded(
          child: _ModeCard(
            icon: Icons.chat_bubble_outline,
            label: '文字模式',
            description: '输入文字回答',
            isSelected: state.selectedMode == 'text',
            onTap: () =>
                context.read<InterviewSetupBloc>().add(const SelectMode('text')),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _ModeCard(
            icon: Icons.mic_outlined,
            label: '语音模式',
            description: '录音回答',
            isSelected: state.selectedMode == 'voice',
            onTap: () => context
                .read<InterviewSetupBloc>()
                .add(const SelectMode('voice')),
          ),
        ),
      ],
    );
  }

  Widget _buildStartButton(BuildContext context, InterviewSetupState state) {
    return FilledButton(
      onPressed: state.canStart && !state.isCreating
          ? () => context.read<InterviewSetupBloc>().add(CreateInterview())
          : null,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 16),
        child: state.isCreating
            ? const SizedBox(
                height: 20,
                width: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: Colors.white,
                ),
              )
            : const Text('开始面试', style: TextStyle(fontSize: 18)),
      ),
    );
  }
}

class _JobRoleCard extends StatelessWidget {
  final JobRole role;
  final bool isSelected;
  final VoidCallback onTap;

  const _JobRoleCard({
    required this.role,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: isSelected ? 4 : 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(
          color: isSelected
              ? Theme.of(context).colorScheme.primary
              : Colors.grey.shade300,
          width: isSelected ? 2 : 1,
        ),
      ),
      color: isSelected
          ? Theme.of(context).colorScheme.primaryContainer.withValues(alpha: 0.3)
          : null,
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                role.nameZh,
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 4),
              Text(
                role.nameEn,
                style: const TextStyle(fontSize: 11, color: Colors.grey),
                textAlign: TextAlign.center,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ModeCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final String description;
  final bool isSelected;
  final VoidCallback onTap;

  const _ModeCard({
    required this.icon,
    required this.label,
    required this.description,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: isSelected ? 4 : 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(
          color: isSelected
              ? Theme.of(context).colorScheme.primary
              : Colors.grey.shade300,
          width: isSelected ? 2 : 1,
        ),
      ),
      color: isSelected
          ? Theme.of(context).colorScheme.primaryContainer.withValues(alpha: 0.3)
          : null,
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Icon(
                icon,
                size: 32,
                color: isSelected
                    ? Theme.of(context).colorScheme.primary
                    : Colors.grey,
              ),
              const SizedBox(height: 8),
              Text(
                label,
                style: TextStyle(
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                description,
                style: const TextStyle(fontSize: 12, color: Colors.grey),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
