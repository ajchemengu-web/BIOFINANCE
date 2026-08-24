import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/networking/api_client.dart';
import '../core/storage/secure_storage.dart';

const _accessTokenKey = 'access_token';
const _refreshTokenKey = 'refresh_token';

/// Login/register + session token persistence. A login attempt that gets a
/// 401 falls back to register — there's no separate sign-up screen yet
/// (docs/roadmap.md still lists a dedicated registration UI as open), so
/// the login form doubles as first-time provisioning for this MVP.
class AuthService {
  AuthService({required this._apiClient, required this._storage});

  final ApiClient _apiClient;
  final TokenStorage _storage;

  Future<void> loginOrRegister(String email, String password, {String? fullName}) async {
    try {
      await _authenticate('/auth/login', {'email': email, 'password': password});
    } on Exception {
      await _authenticate('/auth/register', {
        'email': email,
        'password': password,
        'full_name': fullName ?? email.split('@').first,
      });
    }
  }

  Future<void> _authenticate(String path, Map<String, dynamic> body) async {
    final response = await _apiClient.post(path, body: body) as Map<String, dynamic>;
    final accessToken = response['access_token'] as String;
    final refreshToken = response['refresh_token'] as String;
    await _storage.write(_accessTokenKey, accessToken);
    await _storage.write(_refreshTokenKey, refreshToken);
    _apiClient.setAccessToken(accessToken);
  }

  Future<String?> restoreSession() async {
    final token = await _storage.read(_accessTokenKey);
    _apiClient.setAccessToken(token);
    return token;
  }

  Future<void> logout() async {
    await _storage.delete(_accessTokenKey);
    await _storage.delete(_refreshTokenKey);
    _apiClient.setAccessToken(null);
  }
}

final authServiceProvider = Provider<AuthService>(
  (ref) => AuthService(
    apiClient: ref.watch(apiClientProvider),
    storage: ref.watch(secureStorageProvider),
  ),
);
