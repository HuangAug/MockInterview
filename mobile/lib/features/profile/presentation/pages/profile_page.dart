// Profile page — displays and edits user profile with logout.
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile/features/auth/data/models/auth_user.dart';
import 'package:mobile/features/auth/presentation/bloc/auth_bloc.dart';
import 'package:mobile/features/profile/presentation/bloc/profile_bloc.dart';
import 'package:mobile/features/profile/presentation/bloc/profile_event.dart';
import 'package:mobile/features/profile/presentation/bloc/profile_state.dart';
import 'package:mobile/shared/models/job_role.dart';

class ProfilePage extends StatefulWidget {
  const ProfilePage({super.key});

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  final _displayNameController = TextEditingController();
  String? _selectedJobRoleId;
  bool _initialized = false;

  @override
  void initState() {
    super.initState();
    context.read<ProfileBloc>().add(LoadProfile());
  }

  @override
  void dispose() {
    _displayNameController.dispose();
    super.dispose();
  }

  void _initializeFields(AuthUser user) {
    if (!_initialized) {
      _displayNameController.text = user.displayName;
      _selectedJobRoleId = user.targetJobRoleId;
      _initialized = true;
    }
  }

  void _save() {
    final name = _displayNameController.text.trim();
    if (name.isEmpty || name.length > 50) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('昵称长度需在 1-50 字符之间')),
      );
      return;
    }
    context.read<ProfileBloc>().add(SaveProfile(
          displayName: name,
          targetJobRoleId: _selectedJobRoleId,
        ));
  }

  Future<void> _logout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('退出登录'),
        content: const Text('确定要退出登录吗？'),
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
      // LogoutButtonPressed is defined in auth_bloc.dart (via part)
      context.read<AuthBloc>().add(LogoutButtonPressed());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('个人资料'),
        centerTitle: true,
      ),
      body: BlocConsumer<ProfileBloc, ProfileState>(
        listener: (context, state) {
          if (state is ProfileSaved) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('保存成功'),
                backgroundColor: Color(0xFF22C55E),
              ),
            );
          }
          if (state is ProfileError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.message),
                backgroundColor: Theme.of(context).colorScheme.error,
              ),
            );
          }
        },
        builder: (context, state) {
          if (state is ProfileLoading) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state is ProfileError && _displayNameController.text.isEmpty) {
            return _buildErrorView(context, state.message);
          }

          final user = _extractUser(state);
          final jobRoles = _extractJobRoles(state);
          final isSaving = state is ProfileSaving;

          if (user == null) {
            return const Center(child: CircularProgressIndicator());
          }

          _initializeFields(user);

          return SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Email (read-only)
                TextFormField(
                  initialValue: user.email,
                  enabled: false,
                  decoration: const InputDecoration(
                    labelText: '邮箱',
                    prefixIcon: Icon(Icons.email),
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),

                // Display name (editable)
                TextFormField(
                  controller: _displayNameController,
                  decoration: const InputDecoration(
                    labelText: '昵称',
                    prefixIcon: Icon(Icons.person),
                    border: OutlineInputBorder(),
                    counterText: '',
                  ),
                  maxLength: 50,
                  enabled: !isSaving,
                ),
                const SizedBox(height: 16),

                // Target job role (dropdown)
                DropdownButtonFormField<String?>(
                  initialValue: _selectedJobRoleId,
                  decoration: const InputDecoration(
                    labelText: '目标岗位',
                    prefixIcon: Icon(Icons.work),
                    border: OutlineInputBorder(),
                  ),
                  items: [
                    const DropdownMenuItem<String?>(
                      value: null,
                      child: Text('未选择'),
                    ),
                    ...?jobRoles?.map(
                      (jr) => DropdownMenuItem<String?>(
                        value: jr.id,
                        child: Text(jr.nameZh),
                      ),
                    ),
                  ],
                  onChanged: isSaving
                      ? null
                      : (value) {
                          setState(() {
                            _selectedJobRoleId = value;
                          });
                        },
                ),
                const SizedBox(height: 32),

                // Save button
                FilledButton.icon(
                  onPressed: isSaving ? null : _save,
                  icon: isSaving
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(Icons.save),
                  label: Text(isSaving ? '保存中...' : '保存'),
                ),
                const SizedBox(height: 16),

                // Logout button
                OutlinedButton.icon(
                  onPressed: isSaving ? null : _logout,
                  icon: const Icon(Icons.logout),
                  label: const Text('退出登录'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: const Color(0xFFEF4444),
                    side: const BorderSide(color: Color(0xFFEF4444)),
                  ),
                ),
              ],
            ),
          );
        },
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: 2,
        onDestinationSelected: (index) {
          switch (index) {
            case 0:
              context.go('/home');
            case 1:
              context.go('/history');
            case 2:
              break;
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
                context.read<ProfileBloc>().add(LoadProfile()),
            child: const Text('重试'),
          ),
        ],
      ),
    );
  }

  AuthUser? _extractUser(ProfileState state) {
    if (state is ProfileLoaded) return state.user;
    if (state is ProfileSaving) return state.user;
    if (state is ProfileSaved) return state.user;
    return null;
  }

  List<JobRole>? _extractJobRoles(ProfileState state) {
    if (state is ProfileLoaded) return state.jobRoles;
    if (state is ProfileSaving) return state.jobRoles;
    if (state is ProfileSaved) return state.jobRoles;
    return null;
  }
}
