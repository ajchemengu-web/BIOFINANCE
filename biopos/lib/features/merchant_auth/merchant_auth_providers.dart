import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/errors/app_exception.dart';
import '../../repositories/merchants_repository.dart';

class MerchantSession {
  const MerchantSession({
    this.isSignedIn = false,
    this.isLoading = false,
    this.error,
    this.merchantId,
    this.businessName,
  });

  final bool isSignedIn;
  final bool isLoading;
  final String? error;
  final String? merchantId;
  final String? businessName;

  MerchantSession copyWith({bool? isLoading, String? error}) => MerchantSession(
        isSignedIn: isSignedIn,
        isLoading: isLoading ?? this.isLoading,
        error: error,
        merchantId: merchantId,
        businessName: businessName,
      );
}

/// Merchant "sign-in" is really just POST /merchants — there's no real
/// merchant-auth endpoint yet (Merchant/MerchantDevice have no login;
/// docs/roadmap.md Phase 5), so this creates a fresh Merchant row per
/// sign-in rather than authenticating an existing one. Good enough to get
/// a real merchant_id for payment requests; not real authentication.
class MerchantAuthNotifier extends StateNotifier<MerchantSession> {
  MerchantAuthNotifier(this._merchantsRepository) : super(const MerchantSession());

  final MerchantsRepository _merchantsRepository;

  Future<void> signIn(String businessName) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final merchant = await _merchantsRepository.create(businessName);
      state = MerchantSession(
        isSignedIn: true,
        merchantId: merchant.id,
        businessName: merchant.businessName,
      );
    } on ApiException catch (e) {
      state = state.copyWith(isLoading: false, error: e.message);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: 'Could not reach the BioFinance server');
    }
  }

  void signOut() => state = const MerchantSession();
}

final merchantAuthProvider = StateNotifierProvider<MerchantAuthNotifier, MerchantSession>(
  (ref) => MerchantAuthNotifier(ref.watch(merchantsRepositoryProvider)),
);
