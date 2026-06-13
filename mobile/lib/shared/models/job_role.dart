import 'package:freezed_annotation/freezed_annotation.dart';

part 'job_role.freezed.dart';
part 'job_role.g.dart';

/// JobRoleResponse — matches API §2.3 and backend JobRoleResponse schema.
@freezed
sealed class JobRole with _$JobRole {
  const factory JobRole({
    required String id,
    required String code,
    required String nameZh,
    required String nameEn,
    String? description,
    required int sortOrder,
  }) = _JobRole;

  factory JobRole.fromJson(Map<String, dynamic> json) =>
      _$JobRoleFromJson(json);
}