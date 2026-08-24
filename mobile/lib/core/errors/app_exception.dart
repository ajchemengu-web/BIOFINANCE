/// Base exception type for app-level (non-Flutter-framework) errors, so UI
/// code can catch one type and render a consistent error state.
class AppException implements Exception {
  const AppException(this.message);

  final String message;

  @override
  String toString() => message;
}
