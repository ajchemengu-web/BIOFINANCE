import '../core/networking/api_client.dart';
import '../core/storage/secure_storage.dart';

/// Login/register/refresh + session token persistence. Implemented in Phase 1-2.
class AuthService {
  AuthService({ApiClient? apiClient, SecureStorage? storage})
      : _apiClient = apiClient ?? ApiClient(),
        _storage = storage ?? SecureStorage();

  // ignore: unused_field
  final ApiClient _apiClient;
  // ignore: unused_field
  final SecureStorage _storage;

  Future<void> login(String email, String password) {
    throw UnimplementedError('AuthService.login — implemented in Phase 1/2');
  }
}
