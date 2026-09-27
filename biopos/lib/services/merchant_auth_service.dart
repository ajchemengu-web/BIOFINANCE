import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/networking/api_client.dart';
import '../core/storage/secure_storage.dart';

const _accessTokenKey = 'merchant_access_token';
const _refreshTokenKey = 'merchant_refresh_token';

/// Login/register + session token persistence for a merchant account
/// (docs/roadmap.md Phase 5, "Real merchant authentication"). A login
/// attempt that fails falls back to register — mirrors mobile/lib/services/
/// auth_service.dart's loginOrRegister exactly, so BioPOS's sign-in form
/// doubles as first-time provisioning the same way mobile/'s login form
/// does, rather than inventing a separate registration flow.
class MerchantAuthService {
  MerchantAuthService({required this._apiClient, required this._storage});

  final ApiClient _apiClient;
  final TokenStorage _storage;

  Future<void> loginOrRegister(String businessName, String email, String password) async {
    try {
      await _authenticate('/merchants/login', {'email': email, 'password': password});
    } on Exception {
      await _authenticate('/merchants/register', {
        'business_name': businessName,
        'email': email,
        'password': password,
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

final merchantAuthServiceProvider = Provider<MerchantAuthService>(
  (ref) => MerchantAuthService(
    apiClient: ref.watch(apiClientProvider),
    storage: ref.watch(secureStorageProvider),
  ),
);
