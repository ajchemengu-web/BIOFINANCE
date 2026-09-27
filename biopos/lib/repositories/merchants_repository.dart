import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/networking/api_client.dart';
import '../models/merchant.dart';

/// Registration/login now go through MerchantAuthService (POST /merchants/
/// register and /login return tokens, not a Merchant) — this repository is
/// just the authenticated profile lookup.
class MerchantsRepository {
  MerchantsRepository(this._apiClient);

  final ApiClient _apiClient;

  Future<Merchant> me() async {
    final json = await _apiClient.get('/merchants/me') as Map<String, dynamic>;
    return Merchant.fromJson(json);
  }
}

final merchantsRepositoryProvider =
    Provider<MerchantsRepository>((ref) => MerchantsRepository(ref.watch(apiClientProvider)));
