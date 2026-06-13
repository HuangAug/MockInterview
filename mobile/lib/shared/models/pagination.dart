import 'package:freezed_annotation/freezed_annotation.dart';

part 'pagination.freezed.dart';
part 'pagination.g.dart';

/// Pagination metadata — matches API §1.3 paginated response structure.
@freezed
sealed class Pagination with _$Pagination {
  const factory Pagination({
    required int page,
    required int pageSize,
    required int total,
    required int totalPages,
  }) = _Pagination;

  factory Pagination.fromJson(Map<String, dynamic> json) =>
      _$PaginationFromJson(json);
}

/// Wrapper for paginated list responses.
@freezed
sealed class PaginatedResponse<T> with _$PaginatedResponse<T> {
  // We use a simpler approach — the repository will manually parse
  // paginated responses since Freezed generics with json_serializable
  // require extra boilerplate. This class serves as documentation
  // of the expected shape.
  const factory PaginatedResponse({
    required List<T> items,
    required Pagination pagination,
  }) = _PaginatedResponse<T>;
}