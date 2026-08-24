/// Base exception type for app-level (non-Flutter-framework) errors, so UI
/// code can catch one type and render a consistent error state.
class AppException implements Exception {
  const AppException(this.message);

  final String message;

  @override
  String toString() => message;
}

/// Raised by ApiClient for any non-2xx response. Carries the HTTP status so
/// callers can special-case things like 404/409.
class ApiException extends AppException {
  const ApiException(this.statusCode, String message) : super(message);

  final int statusCode;
}
