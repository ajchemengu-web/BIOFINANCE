import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/networking/api_client.dart';
import '../models/merchant.dart';

/// POST /merchants isn't a real PRD endpoint — it exists so payments have
/// something to target before BioPOS (Phase 5) creates merchants for real.
class MerchantsRepository {
  MerchantsRepository(this._apiClient);

  final ApiClient _apiClient;

  Future<Merchant> create(String businessName) async {
    final json = await _apiClient.post('/merchants', body: {'business_name': businessName})
        as Map<String, dynamic>;
    return Merchant.fromJson(json);
  }
}

final merchantsRepositoryProvider =
    Provider<MerchantsRepository>((ref) => MerchantsRepository(ref.watch(apiClientProvider)));
