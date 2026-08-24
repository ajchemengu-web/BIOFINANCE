import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/networking/api_client.dart';
import '../models/provider_connection.dart';

class ProvidersRepository {
  ProvidersRepository(this._apiClient);

  final ApiClient _apiClient;

  Future<List<ProviderConnection>> list() async {
    final json = await _apiClient.get('/providers') as List;
    return json.map((e) => ProviderConnection.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<ProviderConnection> connect(String providerCode, String externalAccountRef) async {
    final json = await _apiClient.post(
      '/providers/connect',
      body: {'provider_code': providerCode, 'external_account_ref': externalAccountRef},
    ) as Map<String, dynamic>;
    return ProviderConnection.fromJson(json);
  }

  Future<void> disconnect(String connectionId) => _apiClient.delete('/providers/$connectionId');
}

final providersRepositoryProvider =
    Provider<ProvidersRepository>((ref) => ProvidersRepository(ref.watch(apiClientProvider)));
