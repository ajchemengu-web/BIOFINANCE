import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/networking/api_client.dart';
import '../models/provider_catalog_entry.dart';

class ProviderCatalogRepository {
  ProviderCatalogRepository(this._apiClient);

  final ApiClient _apiClient;

  /// Unauthenticated on the backend (reference data, not user data) — works
  /// the same whether called before or after login.
  Future<List<ProviderCatalogEntry>> list() async {
    final json = await _apiClient.get('/provider-catalog') as List;
    return json.map((e) => ProviderCatalogEntry.fromJson(e as Map<String, dynamic>)).toList();
  }
}

final providerCatalogRepositoryProvider =
    Provider<ProviderCatalogRepository>((ref) => ProviderCatalogRepository(ref.watch(apiClientProvider)));
