<?php get_header(); ?>
<main id="main" class="wrap"><section class="hero"><p class="eyebrow">犬の留守番・見守り・暮らし</p><h1>離れている時間も、<br>愛犬に合った見守りを。</h1><p>ペットカメラ・自動給餌器・関連サービスを、機能と費用から比較するためのガイド。</p><a class="button" href="#latest">記事から探す</a></section>
<section aria-labelledby="themes"><h2 id="themes">目的から選ぶ</h2><div class="grid">
<?php foreach (array('ペットカメラ'=>'映像・通知・録画費用を確認。','自動給餌器'=>'容量・お手入れ・停電時の対応を確認。','留守番と関連サービス'=>'環境づくり・シッター・預かりサービスを検討。') as $name=>$description) { ?><div class="card"><h3><?php echo esc_html($name); ?></h3><p><?php echo esc_html($description); ?></p></div><?php } ?>
</div></section><section id="latest"><h2>新着ガイド</h2><div class="grid">
<?php $recent = new WP_Query(array('post_type'=>'post','post_status'=>'publish','posts_per_page'=>6)); if ($recent->have_posts()) { while ($recent->have_posts()) { $recent->the_post(); ?><article><h3><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h3><?php the_excerpt(); ?></article><?php } wp_reset_postdata(); } else { ?><p>記事を準備しています。</p><?php } ?>
</div></section><aside class="notice"><h2>編集方針</h2><p>公式情報と確認日を明示し、比較条件をそろえます。報酬額を理由に順位を変更せず、未確認の体験談や安全性の断定は掲載しません。</p></aside></main><?php get_footer(); ?>
